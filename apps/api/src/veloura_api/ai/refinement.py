import re
from dataclasses import dataclass
from enum import Enum

from veloura_api.ai.preferences import COLOR_WORDS
from veloura_api.models.product import Product, ProductVariant

OutfitLine = tuple[Product, ProductVariant]
RefinedLine = tuple[Product, ProductVariant, str]


class RefinementAction(str, Enum):
    CHEAPER = "cheaper"
    MORE_FORMAL = "more_formal"
    MORE_CASUAL = "more_casual"
    CHANGE_COLOR = "change_color"
    REPLACE_ITEM = "replace_item"


@dataclass
class RefinementIntent:
    action: RefinementAction
    color: str | None = None
    category_hint: str | None = None


CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "shoes": ["shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "heel", "heels", "footwear"],
    "jackets": ["jacket"],
    "coats": ["coat"],
    "tshirts": ["tee", "t-shirt", "tshirt"],
    "shirts": ["shirt", "blouse"],
    "hoodies": ["hoodie"],
    "sweaters": ["sweater", "jumper", "knitwear"],
    "jeans": ["jeans", "denim"],
    "trousers": ["trousers", "pants", "slacks"],
    "shorts": ["shorts"],
    "dresses": ["dress"],
    "skirts": ["skirt"],
    "accessories": ["accessory", "accessories", "bag", "belt", "watch", "sunglasses"],
    "activewear": ["activewear", "leggings", "sports bra"],
    "swimwear": ["swimsuit", "bikini", "trunks"],
}

CHEAPER_PHRASES = [
    "cheaper",
    "less expensive",
    "lower the price",
    "reduce the price",
    "budget option",
    "more affordable",
]
FORMAL_PHRASES = ["more formal", "dressier", "smarter", "more professional", "more polished", "more elegant"]
CASUAL_PHRASES = ["more casual", "more relaxed", "less formal", "dress it down", "more laid back"]
REPLACE_VERBS = ["replace", "swap", "change the", "different", "another", "switch"]


def detect_refinement(message: str) -> RefinementIntent | None:
    """Recognizes explicit refinement commands on an already-generated outfit
    (e.g. 'make it cheaper', 'replace the shoes') so they can be handled as a
    deterministic edit rather than a full from-scratch regeneration."""
    lower = message.lower()

    if any(phrase in lower for phrase in CHEAPER_PHRASES):
        return RefinementIntent(action=RefinementAction.CHEAPER)
    if any(phrase in lower for phrase in FORMAL_PHRASES):
        return RefinementIntent(action=RefinementAction.MORE_FORMAL)
    if any(phrase in lower for phrase in CASUAL_PHRASES):
        return RefinementIntent(action=RefinementAction.MORE_CASUAL)

    if "color" in lower:
        for color in COLOR_WORDS:
            if re.search(rf"\b{color}\b", lower):
                return RefinementIntent(action=RefinementAction.CHANGE_COLOR, color=color)

    if any(verb in lower for verb in REPLACE_VERBS):
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in lower for keyword in keywords):
                return RefinementIntent(action=RefinementAction.REPLACE_ITEM, category_hint=category)

    return None


def _index_candidates_by_category(candidates: list[Product]) -> dict[str, list[Product]]:
    by_category: dict[str, list[Product]] = {}
    for product in candidates:
        by_category.setdefault(product.category.slug, []).append(product)
    return by_category


def _first_in_stock_variant(product: Product) -> ProductVariant | None:
    return next((v for v in product.variants if v.inventory_quantity > 0), None)


def apply_refinement(
    intent: RefinementIntent, current_items: list[OutfitLine], candidates: list[Product]
) -> list[RefinedLine] | None:
    """Applies a refinement to an existing outfit using only real, in-stock
    candidate products. Returns None if nothing could be meaningfully changed,
    so the caller can fall back to a full regeneration instead."""
    by_category = _index_candidates_by_category(candidates)
    changed = False
    result: list[RefinedLine] = []

    if intent.action == RefinementAction.CHEAPER:
        most_expensive = max(current_items, key=lambda pv: pv[0].effective_price)
        for product, variant in current_items:
            if not changed and (product.id, variant.id) == (most_expensive[0].id, most_expensive[1].id):
                cheaper_options = [
                    c
                    for c in by_category.get(product.category.slug, [])
                    if c.id != product.id and c.effective_price < product.effective_price
                ]
                if cheaper_options:
                    cheapest = min(cheaper_options, key=lambda c: c.effective_price)
                    new_variant = _first_in_stock_variant(cheapest)
                    if new_variant:
                        result.append(
                            (cheapest, new_variant, "Swapped in a more budget-friendly alternative.")
                        )
                        changed = True
                        continue
            result.append((product, variant, "Kept from your current look."))

        if not changed and len(current_items) > 2:
            accessory = next((pv for pv in current_items if pv[0].category.slug == "accessories"), None)
            if accessory:
                result = [
                    (p, v, "Kept from your current look.")
                    for p, v in current_items
                    if p.id != accessory[0].id
                ]
                changed = True

    elif intent.action in (RefinementAction.MORE_FORMAL, RefinementAction.MORE_CASUAL):
        target_style = "formal" if intent.action == RefinementAction.MORE_FORMAL else "casual"
        for product, variant in current_items:
            if target_style in {t.lower() for t in product.style_tags}:
                result.append((product, variant, "Kept from your current look."))
                continue
            alternatives = [
                c
                for c in by_category.get(product.category.slug, [])
                if c.id != product.id and target_style in {t.lower() for t in c.style_tags}
            ]
            new_variant = _first_in_stock_variant(alternatives[0]) if alternatives else None
            if alternatives and new_variant:
                result.append((alternatives[0], new_variant, f"A more {target_style} alternative."))
                changed = True
            else:
                result.append((product, variant, "Kept from your current look."))

    elif intent.action == RefinementAction.CHANGE_COLOR:
        for product, variant in current_items:
            same_product_color = next(
                (
                    v
                    for v in product.variants
                    if v.color_name.lower() == intent.color and v.inventory_quantity > 0
                ),
                None,
            )
            if same_product_color:
                result.append((product, same_product_color, f"Now in {intent.color}."))
                changed = True
                continue

            alt_found = None
            for c in by_category.get(product.category.slug, []):
                if c.id == product.id:
                    continue
                v = next(
                    (
                        v
                        for v in c.variants
                        if v.color_name.lower() == intent.color and v.inventory_quantity > 0
                    ),
                    None,
                )
                if v:
                    alt_found = (c, v)
                    break
            if alt_found:
                result.append((alt_found[0], alt_found[1], f"A {intent.color} alternative."))
                changed = True
            else:
                result.append((product, variant, "Kept from your current look (no matching color in stock)."))

    elif intent.action == RefinementAction.REPLACE_ITEM:
        category_hint = intent.category_hint
        for product, variant in current_items:
            if category_hint and product.category.slug == category_hint:
                alternatives = [c for c in by_category.get(category_hint, []) if c.id != product.id]
                if alternatives:
                    choice = alternatives[0]
                    new_variant = _first_in_stock_variant(choice)
                    if new_variant:
                        result.append((choice, new_variant, "Swapped in a fresh alternative."))
                        changed = True
                        continue
            result.append((product, variant, "Kept from your current look."))

    return result if changed else None

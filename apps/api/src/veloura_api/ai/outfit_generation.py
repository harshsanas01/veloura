from pydantic import BaseModel, Field

from veloura_api.ai.client import get_openai_client
from veloura_api.ai.preferences import StylePreferences
from veloura_api.config import get_settings
from veloura_api.models.product import Product

MAX_ITEMS_PER_OUTFIT = 4

# Maps each catalog category to a "body slot" so the heuristic fallback (used when no
# OpenAI key is configured) assembles sensible outfits - e.g. one top + one bottom +
# one layer - instead of combining three unrelated bottoms.
CATEGORY_SLOTS = {
    "tshirts": "top",
    "shirts": "top",
    "hoodies": "top",
    "sweaters": "top",
    "activewear": "top",
    "jeans": "bottom",
    "trousers": "bottom",
    "shorts": "bottom",
    "skirts": "bottom",
    "jackets": "layer",
    "coats": "layer",
    "dresses": "one_piece",
    "swimwear": "one_piece",
    "shoes": "footwear",
    "accessories": "accessory",
}
SLOT_PRIORITY = ["one_piece", "top", "bottom", "layer", "footwear", "accessory"]


class OutfitItemSuggestion(BaseModel):
    product_id: str
    variant_id: str
    reason: str = Field(description="One sentence on why this piece belongs in the outfit.")


class OutfitSuggestion(BaseModel):
    name: str
    explanation: str
    items: list[OutfitItemSuggestion]


class StylistLLMResponse(BaseModel):
    summary: str
    outfits: list[OutfitSuggestion]
    follow_up_suggestions: list[str] = Field(default_factory=list)


GENERATION_SYSTEM_PROMPT = """You are Veloura's AI fashion stylist. You build complete outfits \
STRICTLY from the candidate product list provided in the user message - this is the entire \
live catalog available to recommend from. Never invent a product_id or variant_id that is not \
in the candidate list. Prefer combining 2-4 complementary pieces from different categories \
(e.g. top + bottom + outerwear/shoes) rather than duplicating the same category. Respect the \
stated budget, preferred colors, and excluded colors when choosing items. If the candidate list \
includes an "anchor_product_id" in the preferences, that exact product/variant MUST be included \
as one of the outfit's items, and the rest of the outfit should be built to complement it. If the \
catalog cannot fully satisfy the request, say so plainly in the summary and do the best you can \
with what is available. Explanations should be concise, confident, and editorial in tone."""


def _candidate_payload(products: list[Product], preferences: StylePreferences) -> list[dict]:
    excluded = {c.lower() for c in preferences.excluded_colors}
    preferred = {c.lower() for c in preferences.preferred_colors}
    payload = []
    for p in products:
        variants = [
            {
                "variant_id": str(v.id),
                "size": v.size,
                "color_name": v.color_name,
                "color_hex": v.color_hex,
                "in_stock": v.inventory_quantity > 0,
            }
            for v in p.variants
            if v.inventory_quantity > 0 and v.color_name.lower() not in excluded
        ]
        if not variants:
            continue
        # Surface preferred-color variants first so downstream selection (LLM or
        # heuristic) naturally favors them without needing to inspect every option.
        if preferred:
            variants.sort(key=lambda v: v["color_name"].lower() not in preferred)
        payload.append(
            {
                "product_id": str(p.id),
                "name": p.name,
                "brand": p.brand,
                "category": p.category.slug,
                "gender": p.gender.value,
                "price": p.effective_price,
                "style_tags": p.style_tags,
                "occasion_tags": p.occasion_tags,
                "variants": variants,
                "matches_preferred_color": bool(
                    preferred and any(v["color_name"].lower() in preferred for v in variants)
                ),
            }
        )
    return payload


def _index_by_id(products: list[Product]) -> tuple[dict[str, Product], dict[str, str]]:
    product_map = {str(p.id): p for p in products}
    variant_to_product: dict[str, str] = {}
    for p in products:
        for v in p.variants:
            variant_to_product[str(v.id)] = str(p.id)
    return product_map, variant_to_product


def _validate_and_price(
    llm_response: StylistLLMResponse,
    products: list[Product],
    preferences: StylePreferences,
) -> StylistLLMResponse:
    """Defense in depth: drop any product/variant the model returns that isn't part of the
    real candidate set retrieved from Postgres. This makes hallucinated products impossible
    to reach the frontend even if the model misbehaves."""
    product_map, variant_to_product = _index_by_id(products)
    valid_variant_ids = {str(v.id) for p in products for v in p.variants if v.inventory_quantity > 0}

    cleaned_outfits: list[OutfitSuggestion] = []
    for outfit in llm_response.outfits:
        seen_categories: set[str] = set()
        cleaned_items: list[OutfitItemSuggestion] = []
        for item in outfit.items:
            if item.variant_id not in valid_variant_ids:
                continue
            if variant_to_product.get(item.variant_id) != item.product_id:
                continue
            product = product_map.get(item.product_id)
            if product is None:
                continue
            if product.category.slug in seen_categories and len(cleaned_items) >= 2:
                continue
            seen_categories.add(product.category.slug)
            cleaned_items.append(item)
            if len(cleaned_items) >= MAX_ITEMS_PER_OUTFIT:
                break
        if cleaned_items:
            cleaned_outfits.append(
                OutfitSuggestion(name=outfit.name, explanation=outfit.explanation, items=cleaned_items)
            )

    budget_shortfall = False
    if preferences.budget:

        def outfit_total(outfit: OutfitSuggestion) -> float:
            total = 0.0
            for item in outfit.items:
                product = product_map.get(item.product_id)
                if product:
                    total += product.effective_price
            return total

        within_budget = [o for o in cleaned_outfits if outfit_total(o) <= preferences.budget * 1.05]
        if not within_budget and cleaned_outfits:
            # Fall back to the single cheapest outfit we found and say so plainly,
            # rather than silently exceeding the customer's stated budget.
            cleaned_outfits = [min(cleaned_outfits, key=outfit_total)]
            budget_shortfall = True
        else:
            cleaned_outfits = within_budget

    summary = llm_response.summary
    if budget_shortfall and cleaned_outfits:
        cheapest_total = round(
            sum(product_map[i.product_id].effective_price for i in cleaned_outfits[0].items), 2
        )
        summary = (
            f"We couldn't build a complete look under ${preferences.budget:,.0f} from what's "
            f"currently in stock, so here's our closest option at ${cheapest_total:,.2f}."
        )
    if not cleaned_outfits:
        summary = (
            "Our current collection doesn't have quite the right pieces for that request yet. "
            "Try adjusting your budget, colors, or occasion and I'll take another look."
        )

    return StylistLLMResponse(
        summary=summary,
        outfits=cleaned_outfits,
        follow_up_suggestions=llm_response.follow_up_suggestions
        or ["Make it more casual", "Show me a cheaper version", "Try different colors"],
    )


def _heuristic_generate(products: list[Product], preferences: StylePreferences) -> StylistLLMResponse:
    payload = _candidate_payload(products, preferences)
    if not payload:
        return StylistLLMResponse(
            summary="We couldn't find in-stock pieces matching that request right now.",
            outfits=[],
            follow_up_suggestions=["Try a different occasion", "Increase your budget"],
        )

    # Preferred-color matches first, then cheapest-first so a stated budget is
    # respected whenever the catalog allows it.
    payload = sorted(payload, key=lambda c: (not c["matches_preferred_color"], c["price"]))

    chosen: list[dict] = []
    filled_slots: set[str] = set()
    running_total = 0.0

    if preferences.anchor_product_id:
        anchor_item = next((c for c in payload if c["product_id"] == preferences.anchor_product_id), None)
        if anchor_item:
            chosen.append(anchor_item)
            filled_slots.add(CATEGORY_SLOTS.get(anchor_item["category"], "accessory"))
            running_total += anchor_item["price"]
            payload = [c for c in payload if c["product_id"] != preferences.anchor_product_id]

    for item in payload:
        slot = CATEGORY_SLOTS.get(item["category"], "accessory")
        if slot in filled_slots:
            continue
        if "one_piece" in filled_slots and slot in ("top", "bottom"):
            continue
        if slot == "one_piece" and ({"top", "bottom"} & filled_slots):
            continue
        if preferences.budget and running_total + item["price"] > preferences.budget and chosen:
            continue
        chosen.append(item)
        filled_slots.add(slot)
        running_total += item["price"]
        if len(chosen) >= 3:
            break

    chosen.sort(key=lambda c: SLOT_PRIORITY.index(CATEGORY_SLOTS.get(c["category"], "accessory")))

    items = [
        OutfitItemSuggestion(
            product_id=c["product_id"],
            variant_id=c["variants"][0]["variant_id"],
            reason=(
                "The piece you already have in your cart."
                if c["product_id"] == preferences.anchor_product_id
                else f"A versatile {c['category'].replace('-', ' ')} piece "
                f"that fits the {preferences.occasion} vibe."
            ),
        )
        for c in chosen
    ]
    outfit = OutfitSuggestion(
        name=f"Veloura Edit — {preferences.occasion.title()}",
        explanation=(
            f"A {preferences.style} look assembled from pieces currently in stock, "
            f"suited for {preferences.occasion}."
        ),
        items=items,
    )
    return StylistLLMResponse(
        summary=f"Here's a look for {preferences.occasion} using what's available in our collection.",
        outfits=[outfit],
        follow_up_suggestions=["Make it more casual", "Show me a cheaper version", "Try different colors"],
    )


def generate_outfits(
    products: list[Product], preferences: StylePreferences, history: list[dict] | None = None
) -> StylistLLMResponse:
    candidates = _candidate_payload(products, preferences)
    client = get_openai_client()

    if client is None or not candidates:
        raw = _heuristic_generate(products, preferences)
    else:
        settings = get_settings()
        user_content = (
            f"Customer preferences: {preferences.model_dump_json()}\n\n"
            f"Candidate products (JSON, the ONLY items you may recommend):\n"
            f"{candidates}"
        )
        try:
            completion = client.beta.chat.completions.parse(
                model=settings.openai_chat_model,
                messages=[
                    {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                    *(history or []),  # type: ignore[list-item]
                    {"role": "user", "content": user_content},
                ],
                response_format=StylistLLMResponse,
                temperature=0.4,
            )
            parsed = completion.choices[0].message.parsed
            raw = parsed if parsed is not None else _heuristic_generate(products, preferences)
        except Exception:
            raw = _heuristic_generate(products, preferences)

    return _validate_and_price(raw, products, preferences)


def resolve_outfit_pricing(outfit: OutfitSuggestion, products: list[Product]) -> float:
    product_map = {str(p.id): p for p in products}
    total = 0.0
    for item in outfit.items:
        product = product_map.get(item.product_id)
        if product:
            total += product.effective_price
    return round(total, 2)


__all__ = [
    "OutfitItemSuggestion",
    "OutfitSuggestion",
    "StylistLLMResponse",
    "generate_outfits",
    "resolve_outfit_pricing",
]

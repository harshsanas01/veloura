"""Idempotent seed script for Veloura.

Builds a realistic, gender-correct catalog of 600+ products across 15 categories,
each with multiple size/color variants, an admin account, a sample customer
account, a couple of sample orders, and a couple of saved outfits. Every product
gets a unique primary image from the curated manifest at
scripts/data/product_images.json (validated by `make validate-seed-images`).

Safe to run multiple times - existing rows (matched by slug/email/order number)
are kept, though seed-owned products have their variant images refreshed from
the manifest so an old repeated-image catalog heals in place. Also deactivates
(never deletes) any product left over from an older, narrower generation of this
script so the storefront only shows the current catalog; see
scripts/reseed_products.py to actually purge those rows.

Usage (from apps/api's virtualenv, repo root as cwd):
    python scripts/seed_products.py
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

import random

from sqlalchemy import select
from sqlalchemy.orm import Session
from veloura_api.database import SessionLocal
from veloura_api.models.address import Address
from veloura_api.models.cart import Cart
from veloura_api.models.category import Category
from veloura_api.models.coupon import Coupon, DiscountType
from veloura_api.models.order import Order, OrderItem, OrderStatus
from veloura_api.models.outfit import Outfit, OutfitItem
from veloura_api.models.product import Gender, Product, ProductVariant
from veloura_api.models.user import User, UserRole
from veloura_api.models.wishlist import Wishlist
from veloura_api.security import hash_password
from veloura_api.services.pricing import calculate_order_totals
from veloura_api.utils import slugify

random.seed(42)

CLOTHING_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SHOE_SIZES = ["7", "8", "9", "10", "11", "12"]
ONE_SIZE = ["One Size"]

COLORS = [
    ("Black", "#111111"), ("White", "#FAFAFA"), ("Ivory", "#F1E9D2"), ("Navy", "#1B2A4A"),
    ("Burgundy", "#6E1835"), ("Olive", "#5C6B4A"), ("Camel", "#C19A6B"), ("Charcoal", "#36454F"),
    ("Sage", "#9CAF88"), ("Blush", "#E8C4C4"), ("Denim Blue", "#4A6FA5"), ("Rust", "#B5541A"),
    ("Grey", "#9A9A9A"), ("Cream", "#F5EFE6"), ("Red", "#B33A3A"), ("Forest Green", "#2F4A3C"),
    ("Tan", "#D2B48C"), ("Chocolate", "#4B3221"),
]

# ---------------------------------------------------------------------------
# Brands - fictional Veloura house brands with a consistent identity and price
# tier. KNOWN_SEED_BRANDS lets reseed tooling recognize (and only ever touch)
# catalog rows this script owns, never a real admin-created product.
# ---------------------------------------------------------------------------
BRANDS: dict[str, tuple[str, float]] = {
    "Maison Aster": ("premium minimalist", 1.25),
    "Linden & Co": ("premium minimalist", 1.15),
    "Calder Row": ("contemporary basics", 1.0),
    "Union Thread": ("contemporary basics", 0.95),
    "North & Ash": ("streetwear", 1.05),
    "Kestrel & Vine": ("streetwear", 0.9),
    "Solstice Denim": ("streetwear", 1.0),
    "Ferro Athletics": ("activewear", 1.0),
    "Marchetti": ("formalwear", 1.4),
    "Grayson Field": ("formalwear", 1.3),
    "Etta Moreau": ("resort wear", 1.1),
    "Nomade Atelier": ("resort wear", 1.05),
    "Birch & Bloom": ("sustainable fashion", 1.1),
    "Amaranth Studio": ("sustainable fashion", 1.15),
    "Veloura Studio": ("premium minimalist", 1.2),
}
KNOWN_SEED_BRANDS = set(BRANDS) | {"Ferro Leather", "Aubrey Lane"}  # incl. retired names

CATEGORY_BRAND_AFFINITY: dict[str, list[str]] = {
    "tshirts": ["Calder Row", "Union Thread", "North & Ash", "Birch & Bloom", "Veloura Studio"],
    "shirts": ["Maison Aster", "Linden & Co", "Marchetti", "Calder Row", "Grayson Field"],
    "hoodies": ["North & Ash", "Kestrel & Vine", "Solstice Denim", "Ferro Athletics"],
    "sweaters": ["Maison Aster", "Linden & Co", "Etta Moreau", "Birch & Bloom", "Veloura Studio"],
    "jackets": ["Solstice Denim", "North & Ash", "Kestrel & Vine", "Grayson Field", "Marchetti"],
    "coats": ["Marchetti", "Grayson Field", "Maison Aster", "Linden & Co"],
    "jeans": ["Solstice Denim", "Union Thread", "Calder Row"],
    "trousers": ["Marchetti", "Grayson Field", "Maison Aster", "Calder Row"],
    "shorts": ["Nomade Atelier", "Etta Moreau", "Union Thread", "Ferro Athletics"],
    "activewear": ["Ferro Athletics", "North & Ash", "Kestrel & Vine"],
    "swimwear": ["Nomade Atelier", "Etta Moreau"],
    "shoes": ["Veloura Studio", "North & Ash", "Marchetti", "Ferro Athletics"],
    "accessories": ["Veloura Studio", "Maison Aster", "Amaranth Studio", "Grayson Field"],
    "dresses": ["Maison Aster", "Etta Moreau", "Nomade Atelier", "Amaranth Studio", "Veloura Studio"],
    "skirts": ["Maison Aster", "Etta Moreau", "Amaranth Studio", "Calder Row"],
}

# ---------------------------------------------------------------------------
# Image manifest - every seeded product gets exactly one unique primary image,
# drawn from scripts/data/product_images.json. The manifest holds curated,
# HEAD-verified static Unsplash CDN URLs (never dynamic keyword endpoints),
# grouped by (gender, category) and gender/category-verified against alt text,
# so women's collections only ever draw from women-verified photography and
# vice versa. Images are consumed in manifest order, which keeps assignment
# deterministic across runs; the allocator raises instead of ever recycling an
# image, and `make validate-seed-images` checks the manifest itself.
# ---------------------------------------------------------------------------
IMAGE_MANIFEST_PATH = Path(__file__).resolve().parent / "data" / "product_images.json"


def load_image_pools() -> dict[tuple[str, str], list[dict]]:
    """Group manifest entries by (gender, category slug), preserving order."""
    import json

    manifest = json.loads(IMAGE_MANIFEST_PATH.read_text())
    slug_by_name = {name: slug for slug, name in CATEGORY_NAMES.items()}
    pools: dict[tuple[str, str], list[dict]] = {}
    for entry in manifest["images"]:
        key = (entry["gender"], slug_by_name[entry["category"]])
        pools.setdefault(key, []).append(entry)
    return pools


class ImageAllocator:
    """Hands out each manifest image at most once.

    One product = one unique primary image; a product's size/color variants
    share that image (the variant model carries a single image_url and the
    storefront's primary image is variants[0].image_url). Exhausting a pool is
    a hard error - the manifest must grow before the catalog can.
    """

    def __init__(self) -> None:
        self._pools = load_image_pools()
        self._cursor: dict[tuple[str, str], int] = {}

    def take(self, gender: str, category_slug: str) -> dict:
        key = (gender, category_slug)
        pool = self._pools.get(key, [])
        idx = self._cursor.get(key, 0)
        if idx >= len(pool):
            raise RuntimeError(
                f"Image manifest exhausted for {key} after {idx} image(s); "
                f"add more entries to {IMAGE_MANIFEST_PATH} - images are never reused."
            )
        self._cursor[key] = idx + 1
        return pool[idx]




# ---------------------------------------------------------------------------
# Naming vocabulary - combined combinatorially per (category, gender) so every
# product gets a specific, realistic name (e.g. "Oversized Brushed Cotton
# Hoodie") instead of a numbered placeholder. Each category also carries
# technical material strings, a price band, and default season tags.
# ---------------------------------------------------------------------------
CATEGORY_VOCAB: dict[str, dict] = {
    "tshirts": dict(
        noun={"men": ["Tee", "T-Shirt", "Crewneck Tee"], "women": ["Tee", "T-Shirt", "Fitted Tee"]},
        fit={
            "men": ["Classic", "Slim-Fit", "Relaxed", "Oversized", "Boxy", "Regular-Fit", "Muscle-Fit"],
            "women": ["Fitted", "Cropped", "Oversized", "Relaxed", "Boxy", "Ribbed", "Baby"],
        },
        detail={
            "men": ["Cotton Jersey", "Pima Cotton", "Heavyweight Cotton", "Garment-Dyed", "Washed Cotton", "Slub Cotton", "Waffle-Knit"],
            "women": ["Cotton Jersey", "Pima Cotton", "Modal-Blend", "Ribbed", "Slub Cotton", "Washed Cotton", "Fitted Stretch"],
        },
        materials=["100% organic cotton, 180gsm jersey", "Pima cotton single jersey", "Cotton-modal blend, brushed interior", "Slub cotton jersey"],
        price=(28, 52), seasons=["summer", "spring"],
    ),
    "shirts": dict(
        noun={"men": ["Shirt", "Button-Down", "Poplin Shirt"], "women": ["Shirt", "Blouse", "Button-Down"]},
        fit={
            "men": ["Tailored", "Slim-Fit", "Relaxed", "Classic", "Oxford", "Camp-Collar", "Grandad-Collar"],
            "women": ["Tailored", "Relaxed", "Fitted", "Oversized", "Boyfriend", "Cropped", "Tie-Front"],
        },
        detail={
            "men": ["Cotton Poplin", "Brushed Flannel", "Linen-Cotton", "Oxford Cloth", "Chambray", "Seersucker", "End-on-End Cotton"],
            "women": ["Cotton Poplin", "Silky Satin", "Linen-Blend", "Chambray", "Georgette", "Crepe", "Cotton Voile"],
        },
        materials=["100% cotton poplin", "Linen-cotton blend", "Brushed flannel cotton", "Silky satin-weave polyester"],
        price=(58, 98), seasons=["spring", "summer", "fall"],
    ),
    "hoodies": dict(
        noun={"men": ["Hoodie", "Pullover Hoodie", "Zip Hoodie"], "women": ["Hoodie", "Pullover Hoodie", "Zip Hoodie"]},
        fit={
            "men": ["Heavyweight", "Relaxed", "Oversized", "Classic", "Boxy", "Regular"],
            "women": ["Cropped", "Oversized", "Relaxed", "Fitted", "Boxy"],
        },
        detail={
            "men": ["Brushed Fleece", "French Terry", "Cotton Loopback", "Garment-Dyed Fleece", "Heavyweight Cotton"],
            "women": ["Brushed Fleece", "French Terry", "Ribbed", "Cotton Loopback"],
        },
        materials=["80% cotton, 20% recycled polyester fleece", "100% organic cotton French terry", "Brushed-back cotton loopback"],
        price=(68, 110), seasons=["fall", "winter"],
    ),
    "sweaters": dict(
        noun={"men": ["Sweater", "Jumper", "Pullover"], "women": ["Sweater", "Jumper", "Pullover", "Knit"]},
        fit={
            "men": ["Fisherman", "Ribbed", "Crewneck", "Turtleneck", "Cable-Knit", "Half-Zip", "Shawl-Collar"],
            "women": ["Fine-Knit", "Cropped", "Oversized", "Turtleneck", "Cowl-Neck", "V-Neck", "Cable-Knit"],
        },
        detail={
            "men": ["Merino Wool", "Lambswool", "Cotton-Cashmere", "Chunky Wool", "Alpaca-Blend"],
            "women": ["Merino Wool", "Cashmere-Blend", "Mohair-Blend", "Cotton-Knit", "Ribbed Knit"],
        },
        materials=["100% merino wool", "Cotton-cashmere blend", "Lambswool knit", "Alpaca-blend knit"],
        price=(78, 150), seasons=["fall", "winter"],
    ),
    "jackets": dict(
        noun={"men": ["Jacket", "Blazer"], "women": ["Jacket", "Blazer"]},
        fit={
            "men": ["Bomber", "Moto", "Field", "Trucker", "Utility", "Varsity", "Tailored"],
            "women": ["Bomber", "Moto", "Cropped", "Utility", "Trucker", "Longline", "Tailored"],
        },
        detail={
            "men": ["Full-Grain Leather", "Waxed Cotton Canvas", "Recycled Nylon", "Suede", "Denim", "Wool-Blend"],
            "women": ["Faux Leather", "Waxed Cotton", "Quilted Nylon", "Suede", "Denim", "Wool-Blend"],
        },
        materials=["Full-grain leather", "Waxed cotton canvas", "Wool-blend twill", "Quilted recycled nylon"],
        price=(120, 260), seasons=["fall", "winter", "spring"],
    ),
    "coats": dict(
        noun={"men": ["Coat", "Overcoat"], "women": ["Coat", "Overcoat"]},
        fit={
            "men": ["Tailored Wool", "Long", "Storm", "Duffle", "Car Coat"],
            "women": ["Tailored", "Long", "Belted", "Wrap", "Cocoon"],
        },
        detail={
            "men": ["Wool-Blend Melton", "Waterproof Shell", "Shearling-Lined Suede", "Cotton Twill"],
            "women": ["Wool-Blend Melton", "Shearling-Lined Suede", "Waterproof Shell", "Faux Fur-Trim"],
        },
        materials=["Wool-blend melton", "Shearling-lined suede", "Technical waterproof shell", "Cotton twill"],
        price=(180, 340), seasons=["winter", "fall"],
    ),
    "jeans": dict(
        noun={"men": ["Jean", "Denim"], "women": ["Jean", "Denim"]},
        fit={
            "men": ["Slim-Fit", "Straight-Leg", "Relaxed", "Athletic-Fit", "Tapered", "Bootcut"],
            "women": ["High-Rise Skinny", "Straight-Leg", "Wide-Leg", "Mom-Fit", "Bootcut", "Slim-Straight"],
        },
        detail={
            "men": ["Stretch Selvedge Denim", "Rigid Organic Denim", "Washed Denim", "Raw Denim"],
            "women": ["Stretch Denim", "Rigid Organic Denim", "Washed Denim"],
        },
        materials=["Stretch selvedge denim", "Rigid organic cotton denim", "Washed comfort-stretch denim"],
        price=(78, 138), seasons=["fall", "spring"],
    ),
    "trousers": dict(
        noun={"men": ["Trouser", "Pant"], "women": ["Trouser", "Pant"]},
        fit={
            "men": ["Tailored", "Pleated", "Slim", "Wide-Leg", "Straight-Leg", "Suit"],
            "women": ["Tailored", "Wide-Leg", "Straight-Leg", "High-Rise", "Cigarette", "Palazzo"],
        },
        detail={
            "men": ["Italian Wool-Blend", "Stretch Cotton Twill", "Flannel Wool", "Linen-Blend"],
            "women": ["Stretch Cotton Twill", "Wool-Blend", "Linen-Blend", "Crepe"],
        },
        materials=["Italian wool-blend suiting", "Stretch cotton twill", "Flannel wool", "Linen-blend"],
        price=(68, 140), seasons=["fall", "spring"],
    ),
    "shorts": dict(
        noun={"men": ["Short", "Chino Short"], "women": ["Short", "Chino Short"]},
        fit={
            "men": ["Tailored", "Drawstring", "Classic", "Cargo", "Chino"],
            "women": ["Tailored", "High-Rise", "Bermuda", "Drawstring", "Paperbag"],
        },
        detail={
            "men": ["Cotton Twill", "Stretch Chino", "Linen-Blend"],
            "women": ["Cotton Twill", "Stretch Chino", "Linen-Blend"],
        },
        materials=["Cotton twill", "Stretch cotton chino", "Linen-blend"],
        price=(48, 82), seasons=["summer", "spring"],
    ),
    "activewear": dict(
        noun={
            "men": ["Performance Tee", "Training Tank", "Training Jogger", "Running Short", "Performance Half-Zip"],
            "women": ["Sports Bra", "Training Legging", "Studio Tank", "Training Jogger", "Performance Bra"],
        },
        fit={
            "men": ["Training", "Run", "Studio", "Performance", "Compression"],
            "women": ["Training", "Studio", "Run", "High-Support", "Seamless"],
        },
        detail={
            "men": ["Moisture-Wicking Polyester", "Brushed Technical Knit", "Recycled Performance Mesh"],
            "women": ["Moisture-Wicking Polyester", "Recycled Performance Mesh", "Ribbed Compression"],
        },
        materials=["Moisture-wicking recycled polyester", "Brushed technical knit", "Compression performance mesh"],
        price=(38, 98), seasons=["summer", "spring", "fall"],
    ),
    "swimwear": dict(
        noun={"men": ["Swim Short", "Board Short", "Swim Trunk"], "women": ["Swimsuit", "Bikini Set", "One-Piece"]},
        fit={
            "men": ["Resort", "Classic", "Printed", "Tailored"],
            "women": ["High-Waist", "Classic", "Printed", "Ruched", "Halter"],
        },
        detail={
            "men": ["Quick-Dry Recycled Nylon"],
            "women": ["Quick-Dry Recycled Nylon", "Ribbed Swim Fabric"],
        },
        materials=["Quick-dry recycled nylon-elastane", "Ribbed swim fabric"],
        price=(48, 98), seasons=["summer"],
    ),
    "shoes": dict(
        noun={"men": ["Sneaker", "Boot", "Loafer", "Derby"], "women": ["Sneaker", "Boot", "Heel", "Flat", "Mule"]},
        fit={
            "men": ["Court", "Trail", "Everyday", "Minimalist", "Leather"],
            "women": ["Court", "Everyday", "Minimalist", "Block-Heel", "Pointed-Toe"],
        },
        detail={
            "men": ["Full-Grain Leather", "Knit Mesh Upper", "Suede"],
            "women": ["Full-Grain Leather", "Knit Mesh Upper", "Suede"],
        },
        materials=["Full-grain leather", "Knit mesh upper", "Suede"],
        price=(98, 220), seasons=["fall", "spring", "summer"],
    ),
    "accessories": dict(
        noun={
            "men": ["Belt", "Wallet", "Watch", "Sunglasses", "Cap", "Crossbody Bag"],
            "women": ["Handbag", "Clutch", "Sunglasses", "Scarf", "Belt", "Jewelry Set", "Tote"],
        },
        fit={
            "men": ["Signature", "Classic", "Woven", "Minimalist"],
            "women": ["Signature", "Classic", "Woven", "Structured"],
        },
        detail={
            "men": ["Italian Leather", "Brushed Stainless Steel", "Merino Wool"],
            "women": ["Italian Leather", "Brushed Gold-Tone Metal", "Silk"],
        },
        materials=["Italian leather", "Brushed stainless steel", "Silk twill", "Merino wool"],
        price=(38, 180), seasons=["fall", "spring", "summer", "winter"],
    ),
    "dresses": dict(
        noun={"women": ["Dress"]},
        fit={
            "women": ["Wrap", "Slip", "Midi", "Off-Shoulder", "Tailored", "Bodycon", "Fit-and-Flare",
                       "Shirt", "Halter", "Cowl-Neck", "A-Line", "Faux-Wrap", "Puff-Sleeve", "Maxi", "Mini"],
        },
        detail={
            "women": ["Silk Crepe", "Cotton Poplin", "Stretch Jersey", "Satin", "Linen-Blend", "Ribbed Knit", "Georgette"],
        },
        materials=["Silk crepe", "Cotton poplin", "Stretch jersey", "Satin", "Linen-blend", "Georgette"],
        price=(88, 240), seasons=["spring", "summer", "fall"],
    ),
    "skirts": dict(
        noun={"women": ["Skirt"]},
        fit={"women": ["A-Line", "Pleated", "Midi", "Wrap", "Mini", "Maxi", "Bias-Cut", "Tiered", "Pencil"]},
        detail={"women": ["Wool-Blend", "Cotton Twill", "Satin", "Denim", "Linen-Blend"]},
        materials=["Wool-blend", "Cotton twill", "Satin", "Denim", "Linen-blend"],
        price=(68, 130), seasons=["spring", "summer", "fall"],
    ),
}

CARE_INSTRUCTIONS = {
    "tshirts": "Machine wash cold with like colors, tumble dry low, do not bleach.",
    "shirts": "Machine wash cold, hang to dry or tumble dry low, warm iron if needed.",
    "hoodies": "Machine wash cold inside out, tumble dry low, do not iron over print.",
    "sweaters": "Hand wash cold or dry clean, lay flat to dry, do not wring.",
    "jackets": "Wipe clean or spot treat; leather and suede pieces should be professionally cleaned.",
    "coats": "Dry clean only, store on a padded hanger.",
    "jeans": "Machine wash cold inside out, tumble dry low, wash sparingly to preserve color.",
    "trousers": "Dry clean or machine wash cold on a gentle cycle, hang to dry.",
    "shorts": "Machine wash cold, tumble dry low.",
    "activewear": "Machine wash cold, do not use fabric softener, hang or tumble dry low.",
    "swimwear": "Rinse in cold water after each wear, hand wash, lay flat to dry, avoid direct sun.",
    "shoes": "Wipe clean with a soft, dry cloth; treat leather with conditioner as needed.",
    "accessories": "Wipe clean with a soft cloth; store away from direct sunlight and moisture.",
    "dresses": "Dry clean or hand wash cold depending on fabric; hang to dry.",
    "skirts": "Dry clean or machine wash cold on a gentle cycle, hang to dry.",
}

OCCASIONS = ["casual", "date-night", "pool-party", "business-casual", "streetwear",
             "minimal", "all-black", "vacation", "wedding", "party", "active", "formal"]
STYLES = ["casual", "formal", "business-casual", "streetwear", "minimal"]

DESCRIPTION_TEMPLATES = [
    "Cut from {material} for a considered drape, the {name} brings {brand}'s quiet, "
    "editorial sensibility to {occasion} dressing. Finished with clean seams and a "
    "fit that layers effortlessly with the rest of your wardrobe.",
    "The {name} is built from {material} and designed to move with you - a versatile "
    "piece that reads polished for {occasion} without trying too hard. A Veloura "
    "wardrobe staple in the making.",
    "{brand} reworks a classic silhouette in {material}. The {name} balances structure "
    "and comfort, making it just as easy to dress up for {occasion} as it is to keep "
    "in weekly rotation.",
    "An essential from {brand}, the {name} takes {material} and pares it back to what "
    "matters: fit, texture, and durability. Style it for {occasion} or fold it into "
    "an everyday rotation - either way, it holds its shape wear after wear.",
    "Designed in {material}, the {name} is {brand}'s take on modern ease - considered "
    "proportions, a quietly confident finish, and enough range to move from {occasion} "
    "into whatever the rest of your day calls for.",
    "{brand}'s {name} pairs {material} with a fit that flatters without fuss, striking "
    "the balance between {occasion} polish and everyday comfort.",
]


def make_description(name: str, brand: str, material: str, occasion: str) -> str:
    template = random.choice(DESCRIPTION_TEMPLATES)
    return template.format(name=name, brand=brand, material=material, occasion=occasion)


def make_short_description(cat_name: str, material: str) -> str:
    singular = cat_name[:-1] if cat_name.endswith("s") and cat_name.lower() != "accessories" else cat_name
    return f"A refined {singular.lower()} in {material.lower()}."


def get_or_create_category(db: Session, slug: str, name: str) -> Category:
    existing = db.scalar(select(Category).where(Category.slug == slug))
    if existing:
        return existing
    category = Category(slug=slug, name=name, description=f"Shop {name.lower()} at Veloura.")
    db.add(category)
    db.flush()
    return category


CATEGORY_NAMES = {
    "tshirts": "T-Shirts", "shirts": "Shirts", "hoodies": "Hoodies", "sweaters": "Sweaters",
    "jackets": "Jackets", "coats": "Coats", "jeans": "Jeans", "trousers": "Trousers",
    "shorts": "Shorts", "activewear": "Activewear", "swimwear": "Swimwear", "shoes": "Shoes",
    "accessories": "Accessories", "dresses": "Dresses", "skirts": "Skirts",
}

# Target catalog volume: 13 shared categories get >=20 per gender (men get extra
# depth in shirts/jackets/trousers/activewear/accessories to make up for the two
# women-exclusive categories below, per spec); dresses/skirts are women-only.
CATEGORY_COUNTS: dict[str, dict[str, int]] = {
    "tshirts": {"men": 20, "women": 20},
    "shirts": {"men": 28, "women": 20},
    "hoodies": {"men": 20, "women": 20},
    "sweaters": {"men": 20, "women": 20},
    "jackets": {"men": 30, "women": 20},
    "coats": {"men": 20, "women": 20},
    "jeans": {"men": 20, "women": 20},
    "trousers": {"men": 28, "women": 20},
    "shorts": {"men": 20, "women": 20},
    "activewear": {"men": 26, "women": 20},
    "swimwear": {"men": 20, "women": 20},
    "shoes": {"men": 20, "women": 20},
    "accessories": {"men": 26, "women": 20},
    "dresses": {"women": 22},
    "skirts": {"women": 22},
}
UNISEX_ACCESSORY_COUNT = 6

UNISEX_ACCESSORY_ITEMS = [
    ("Signature Leather Belt", "Italian full-grain leather"),
    ("Classic Aviator Sunglasses", "Acetate frame, polarized lenses"),
    ("Ribbed Merino Beanie", "100% merino wool"),
    ("Structured Crossbody Bag", "Italian leather, brushed hardware"),
    ("Minimalist Field Watch", "Brushed stainless steel, sapphire crystal"),
    ("Everyday Canvas Tote", "Organic cotton canvas"),
    ("Woven Silk Scarf", "100% silk twill"),
    ("Classic Wool Cap", "Merino wool blend"),
]


def _generate_names(gender: str, vocab: dict, count: int) -> list[str]:
    fits = vocab["fit"][gender]
    details = vocab["detail"][gender]
    nouns = vocab["noun"][gender]
    combos = list(itertools.product(fits, details, nouns))
    random.shuffle(combos)

    names: list[str] = []
    seen: set[str] = set()
    pattern_cycle = itertools.cycle(["fit_noun", "fit_detail_noun", "detail_noun"])
    for fit, detail, noun in combos:
        if len(names) >= count:
            break
        pattern = next(pattern_cycle)
        if pattern == "fit_noun":
            name = f"{fit} {noun}"
        elif pattern == "detail_noun":
            name = f"{detail} {noun}"
        else:
            name = f"{fit} {detail} {noun}"
        if name in seen:
            continue
        seen.add(name)
        names.append(name)

    # Extremely small vocab spaces (shouldn't happen given the lists above) -
    # pad deterministically rather than crash.
    i = 0
    while len(names) < count:
        fit, detail, noun = combos[i % len(combos)]
        name = f"{fit} {detail} {noun} No. {i + 2}"
        if name not in seen:
            seen.add(name)
            names.append(name)
        i += 1
    return names[:count]


def build_products_for(
    gender: str, category_slug: str, count: int, images: ImageAllocator
) -> list[dict]:
    vocab = CATEGORY_VOCAB[category_slug]
    cat_name = CATEGORY_NAMES[category_slug]
    names = _generate_names(gender, vocab, count)
    brand_pool = CATEGORY_BRAND_AFFINITY[category_slug]

    size_type = "shoes" if category_slug == "shoes" else ("accessory" if category_slug == "accessories" else "clothing")
    size_list = {"clothing": CLOTHING_SIZES, "shoes": SHOE_SIZES, "accessory": ONE_SIZE}[size_type]

    products = []
    for i, name in enumerate(names):
        brand = brand_pool[i % len(brand_pool)]
        direction, multiplier = BRANDS[brand]
        material = vocab["materials"][i % len(vocab["materials"])]
        occasion = random.choice(OCCASIONS)
        style = direction if direction in STYLES else random.choice(STYLES)

        low, high = vocab["price"]
        base_price = round(random.uniform(low, high) * multiplier, 2)
        on_sale = random.random() < 0.22
        sale_price = round(base_price * random.choice([0.7, 0.75, 0.8, 0.85]), 2) if on_sale else None

        season_tags = vocab["seasons"]
        occasion_tags = sorted({occasion, random.choice(OCCASIONS)})
        style_tags = sorted({style, random.choice(STYLES)})

        num_colors = 1 if size_type == "accessory" else 2
        colors = random.sample(COLORS, k=num_colors)

        image = images.take(gender, category_slug)
        variants = []
        for c_idx, (color_name, color_hex) in enumerate(colors):
            for size in size_list:
                sku = f"{category_slug[:3].upper()}-{gender[:1].upper()}{i:03d}{c_idx}-{size}".replace(" ", "")
                variants.append(dict(
                    sku=sku,
                    size=size,
                    color_name=color_name,
                    color_hex=color_hex,
                    inventory_quantity=random.choice([0, 2, 4, 8, 15, 25, 40]),
                    image_url=image["url"],
                ))

        products.append(dict(
            image_source_id=image["source_id"],
            name=name,
            brand=brand,
            gender=gender,
            category_slug=category_slug,
            category_name=cat_name,
            base_price=base_price,
            sale_price=sale_price,
            material=material.capitalize(),
            care_instructions=CARE_INSTRUCTIONS[category_slug],
            occasion_tags=occasion_tags,
            style_tags=style_tags,
            season_tags=season_tags,
            is_featured=random.random() < 0.15,
            description=make_description(name, brand, material, occasion.replace("-", " ")),
            short_description=make_short_description(cat_name, material),
            variants=variants,
        ))
    return products


def build_unisex_accessories(images: ImageAllocator) -> list[dict]:
    products = []
    brand_pool = CATEGORY_BRAND_AFFINITY["accessories"]
    for i, (name, material) in enumerate(UNISEX_ACCESSORY_ITEMS[:UNISEX_ACCESSORY_COUNT]):
        brand = brand_pool[i % len(brand_pool)]
        _, multiplier = BRANDS[brand]
        occasion = random.choice(OCCASIONS)
        base_price = round(random.uniform(38, 180) * multiplier, 2)
        on_sale = random.random() < 0.2
        sale_price = round(base_price * 0.8, 2) if on_sale else None
        colors = random.sample(COLORS, k=1)
        image = images.take("unisex", "accessories")
        variants = []
        for c_idx, (color_name, color_hex) in enumerate(colors):
            sku = f"ACU-{i:03d}{c_idx}-OS"
            variants.append(dict(
                sku=sku, size="One Size", color_name=color_name, color_hex=color_hex,
                inventory_quantity=random.choice([0, 4, 12, 25]),
                image_url=image["url"],
            ))
        products.append(dict(
            image_source_id=image["source_id"],
            name=name, brand=brand, gender="unisex", category_slug="accessories",
            category_name="Accessories", base_price=base_price, sale_price=sale_price,
            material=material, care_instructions=CARE_INSTRUCTIONS["accessories"],
            occasion_tags=[occasion], style_tags=["minimal", "casual"],
            season_tags=["fall", "spring", "summer", "winter"],
            is_featured=random.random() < 0.15,
            description=make_description(name, brand, material, occasion.replace("-", " ")),
            short_description=make_short_description("Accessories", material),
            variants=variants,
        ))
    return products


def build_products() -> list[dict]:
    # Re-seed so the catalog (names -> slugs -> SKUs) is identical no matter
    # how many times this is called in one process (validation runs it too).
    random.seed(42)
    images = ImageAllocator()
    products: list[dict] = []
    for category_slug, gender_counts in CATEGORY_COUNTS.items():
        for gender, count in gender_counts.items():
            products.extend(build_products_for(gender, category_slug, count, images))
    products.extend(build_unisex_accessories(images))
    assert_unique_primary_images(products)
    return products


def assert_unique_primary_images(products: list[dict]) -> None:
    """Fail the seed outright if any two products would share an image."""
    primary_urls = [p["variants"][0]["image_url"] for p in products]
    assert len(primary_urls) == len(set(primary_urls)), "duplicate primary image URLs in seed"
    source_ids = [p["image_source_id"] for p in products]
    assert len(source_ids) == len(set(source_ids)), "duplicate image source_ids in seed"
    for p in products:
        urls = {v["image_url"] for v in p["variants"]}
        assert urls == {p["variants"][0]["image_url"]}, (
            f"variants of {p['name']} must share the product's one manifest image"
        )
        assert all(v["image_url"] for v in p["variants"]), f"empty image_url on {p['name']}"


def seed_products(db: Session) -> list[Product]:
    categories = {
        slug: get_or_create_category(db, slug, name) for slug, name in CATEGORY_NAMES.items()
    }
    db.commit()

    all_new_slugs: set[str] = set()
    refreshed_slugs: set[str] = set()
    created: list[Product] = []
    for data in build_products():
        base_slug = slugify(f"{data['brand']} {data['name']} {data['gender']}")
        slug = base_slug
        suffix = 2
        while slug in all_new_slugs:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        all_new_slugs.add(slug)

        existing = db.scalar(select(Product).where(Product.slug == slug))
        if existing:
            # Refresh images in place so re-running the seed repairs catalogs
            # created before the unique-image manifest existed, without ever
            # deleting the product (orders, carts, and reviews stay intact).
            new_url = data["variants"][0]["image_url"]
            for variant in existing.variants:
                if variant.image_url != new_url:
                    variant.image_url = new_url
                    refreshed_slugs.add(slug)
            created.append(existing)
            continue

        product = Product(
            slug=slug,
            name=data["name"],
            brand=data["brand"],
            description=data["description"],
            short_description=data["short_description"],
            gender=Gender(data["gender"]),
            category_id=categories[data["category_slug"]].id,
            base_price=data["base_price"],
            sale_price=data["sale_price"],
            material=data["material"],
            care_instructions=data["care_instructions"],
            occasion_tags=data["occasion_tags"],
            style_tags=data["style_tags"],
            season_tags=data["season_tags"],
            is_featured=data["is_featured"],
            is_active=True,
        )
        for v in data["variants"]:
            product.variants.append(ProductVariant(**v))
        db.add(product)
        db.flush()
        created.append(product)
    db.commit()
    if refreshed_slugs:
        print(f"  -> refreshed images on {len(refreshed_slugs)} existing product(s) from the manifest.")

    # Superseded rows from an older/narrower run of this script are deactivated
    # (never deleted - see scripts/reseed_products.py for an explicit, opt-in
    # purge) so the storefront only ever shows the current catalog.
    stale = db.scalars(
        select(Product).where(
            Product.brand.in_(KNOWN_SEED_BRANDS),
            Product.slug.not_in(all_new_slugs),
            Product.is_active.is_(True),
        )
    ).all()
    for product in stale:
        product.is_active = False
    if stale:
        db.commit()
        print(f"  -> deactivated {len(stale)} superseded product(s) from an older seed run.")

    return created


def seed_users(db: Session) -> tuple[User, User]:
    admin = db.scalar(select(User).where(User.email == "admin@veloura.com"))
    if not admin:
        admin = User(
            email="admin@veloura.com",
            hashed_password=hash_password("AdminPass123!"),
            first_name="Veloura",
            last_name="Admin",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.flush()
        db.add(Cart(user_id=admin.id))
        db.add(Wishlist(user_id=admin.id))

    customer = db.scalar(select(User).where(User.email == "customer@veloura.com"))
    if not customer:
        customer = User(
            email="customer@veloura.com",
            hashed_password=hash_password("CustomerPass123!"),
            first_name="Ava",
            last_name="Customer",
            role=UserRole.CUSTOMER,
        )
        db.add(customer)
        db.flush()
        db.add(Cart(user_id=customer.id))
        db.add(Wishlist(user_id=customer.id))
        db.add(
            Address(
                user_id=customer.id,
                full_name="Ava Customer",
                line1="128 Rivington Street",
                line2="Apt 4B",
                city="New York",
                state="NY",
                postal_code="10002",
                country="United States",
                phone="+1 212 555 0199",
                is_default_shipping=True,
                is_default_billing=True,
            )
        )
    db.commit()
    return admin, customer


def seed_orders(db: Session, customer: User, products: list[Product]) -> None:
    existing = db.scalar(select(Order).where(Order.user_id == customer.id))
    if existing:
        return

    in_stock_variants = [
        (p, v) for p in products for v in p.variants if v.inventory_quantity > 3
    ]
    if len(in_stock_variants) < 4:
        return

    sample = random.sample(in_stock_variants, k=4)
    address = {
        "full_name": "Ava Customer",
        "line1": "128 Rivington Street",
        "line2": "Apt 4B",
        "city": "New York",
        "state": "NY",
        "postal_code": "10002",
        "country": "United States",
        "phone": "+1 212 555 0199",
    }

    for order_idx, chunk in enumerate([sample[:2], sample[2:]]):
        subtotal = sum(p.effective_price for p, _ in chunk)
        totals = calculate_order_totals(subtotal)
        order_number = f"VLR{100000 + order_idx + 1}"
        if db.scalar(select(Order).where(Order.order_number == order_number)):
            continue
        order = Order(
            user_id=customer.id,
            order_number=order_number,
            status=OrderStatus.DELIVERED if order_idx == 0 else OrderStatus.PROCESSING,
            shipping_address=address,
            **totals,
        )
        db.add(order)
        db.flush()
        for product, variant in chunk:
            db.add(
                OrderItem(
                    order_id=order.id,
                    variant_id=variant.id,
                    product_name=product.name,
                    variant_size=variant.size,
                    variant_color=variant.color_name,
                    unit_price=product.effective_price,
                    quantity=1,
                )
            )
    db.commit()


def seed_outfits(db: Session, customer: User, products: list[Product]) -> None:
    existing = db.scalar(select(Outfit).where(Outfit.user_id == customer.id))
    if existing:
        return

    by_category: dict[str, list[Product]] = {}
    for p in products:
        by_category.setdefault(p.category.slug if p.category else "", []).append(p)

    candidates = []
    for slug in ["tshirts", "trousers", "jackets"]:
        pool = [p for p in by_category.get(slug, []) if any(v.inventory_quantity > 0 for v in p.variants)]
        if pool:
            candidates.append(random.choice(pool))

    if len(candidates) < 2:
        return

    total = sum(p.effective_price for p in candidates)
    outfit = Outfit(
        session_id=None,
        user_id=customer.id,
        name="Styled by Veloura — City Weekend",
        explanation="A relaxed, editorial layering look built for a weekend in the city.",
        total_price=round(total, 2),
    )
    db.add(outfit)
    db.flush()
    for p in candidates:
        variant = next(v for v in p.variants if v.inventory_quantity > 0)
        db.add(
            OutfitItem(
                outfit_id=outfit.id,
                product_id=p.id,
                variant_id=variant.id,
                reason=f"Adds a versatile {p.category.name.lower()} layer to the look.",
            )
        )
    db.commit()


def seed_reviews(db: Session, customer: User, products: list[Product]) -> None:
    from veloura_api.models.review import Review

    existing = db.scalar(select(Review).where(Review.user_id == customer.id))
    if existing:
        return

    reviewable = [p for p in products if p.is_active][:3]
    sample_reviews = [
        (5, "Exactly as pictured", "The fit and fabric are even better in person. Ordering another color."),
        (4, "Great everyday piece", "Comfortable and holds up well after a few washes. True to size."),
        (3, "Good but runs small", "Nice material, but I'd size up if you're between sizes."),
    ]
    for product, (rating, title, body) in zip(reviewable, sample_reviews, strict=False):
        db.add(
            Review(
                product_id=product.id,
                user_id=customer.id,
                rating=rating,
                title=title,
                body=body,
                is_verified_purchase=True,
            )
        )
    db.commit()


def seed_coupons(db: Session) -> None:
    demo_coupons = [
        dict(
            code="WELCOME10",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=10,
            free_shipping=False,
            min_order_value=None,
            max_discount=None,
            usage_limit=None,
            per_user_limit=1,
        ),
        dict(
            code="STYLE20",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=20,
            free_shipping=False,
            min_order_value=150,
            max_discount=75,
            usage_limit=None,
            per_user_limit=None,
        ),
        dict(
            code="FREESHIP",
            discount_type=DiscountType.FIXED,
            discount_value=0,
            free_shipping=True,
            min_order_value=50,
            max_discount=None,
            usage_limit=None,
            per_user_limit=None,
        ),
    ]
    for data in demo_coupons:
        existing = db.scalar(select(Coupon).where(Coupon.code == data["code"]))
        if existing:
            continue
        db.add(Coupon(is_active=True, applicable_categories=[], applicable_products=[], **data))
    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        print("Seeding categories and products...")
        products = seed_products(db)
        print(f"  -> {len(products)} products in catalog.")

        print("Seeding users...")
        admin, customer = seed_users(db)
        print(f"  -> admin: {admin.email}, customer: {customer.email}")

        print("Seeding sample orders...")
        seed_orders(db, customer, products)

        print("Seeding sample outfits...")
        seed_outfits(db, customer, products)

        print("Seeding sample reviews...")
        seed_reviews(db, customer, products)

        print("Seeding demo coupons...")
        seed_coupons(db)

        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""Idempotent seed script for Veloura.

Creates categories, 60+ products with realistic copy and multiple size/color
variants, an admin account, a sample customer account, a couple of sample
orders, and a couple of saved outfits. Safe to run multiple times - existing
rows (matched by slug/email/order number) are left untouched.

Usage (from apps/api's virtualenv, repo root as cwd):
    python scripts/seed_products.py
"""

from __future__ import annotations

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
    ("Black", "#111111"),
    ("White", "#FAFAFA"),
    ("Ivory", "#F1E9D2"),
    ("Navy", "#1B2A4A"),
    ("Burgundy", "#6E1835"),
    ("Olive", "#5C6B4A"),
    ("Camel", "#C19A6B"),
    ("Charcoal", "#36454F"),
    ("Sage", "#9CAF88"),
    ("Blush", "#E8C4C4"),
    ("Denim Blue", "#4A6FA5"),
    ("Rust", "#B5541A"),
    ("Grey", "#9A9A9A"),
    ("Cream", "#F5EFE6"),
    ("Red", "#B33A3A"),
]

BRANDS = [
    "Veloura Studio", "North & Ash", "Maison Aster", "Calder Row", "Linden & Co",
    "Solstice Denim", "Ferro Leather", "Aubrey Lane", "Marchetti", "Nomade Atelier",
    "Birch & Bloom", "Grayson Field", "Etta Moreau", "Kestrel & Vine", "Union Thread",
]

IMG = "https://images.unsplash.com/photo-{}?w=900&q=80"

IMAGE_POOL: dict[str, list[str]] = {
    "tshirts": [IMG.format(i) for i in [
        "1503341504253-dff4815485f1", "1521572163474-6864f9cf17ab", "1562157873-818bc0726f68",
        "1576566588028-4147f3842f27", "1583743814966-8936f5b7be1a", "1618354691373-d851c5c3a990",
        "1622470953794-aa9c70b0fb9d", "1554568218-0f1715e72254",
    ]],
    "shirts": [IMG.format(i) for i in [
        "1602810318383-e386cc2a3ccf", "1596755094514-f87e34085b2c", "1523381210434-271e8be1f52b",
    ]],
    "hoodies": [IMG.format(i) for i in [
        "1548126032-079a0fb0099d", "1550246140-29f40b909e5a", "1620799140408-edc6dcb6d633",
    ]],
    "sweaters": [IMG.format(i) for i in [
        "1434389677669-e08b4cac3105", "1620799140408-edc6dcb6d633",
    ]],
    "jackets": [IMG.format(i) for i in [
        "1487222477894-8943e31ef7b2", "1516257984-b1b4d707412e", "1548883354-94bcfe321cbb",
        "1591047139829-d91aecb6caea", "1580657018950-c7f7d6a6d990", "1608063615781-e2ef8c73d114",
    ]],
    "coats": [IMG.format(i) for i in [
        "1483985988355-763728e1935b", "1580657018950-c7f7d6a6d990", "1608063615781-e2ef8c73d114",
    ]],
    "jeans": [IMG.format(i) for i in [
        "1560243563-062bfc001d68", "1622470953794-aa9c70b0fb9d",
    ]],
    "trousers": [IMG.format(i) for i in [
        "1509631179647-0177331693ae", "1594633312681-425c7b97ccd1", "1594938298603-c8148c4dae35",
        "1544441893-675973e31985",
    ]],
    "shorts": [IMG.format(i) for i in [
        "1591195853828-11db59a44f6b",
    ]],
    "activewear": [IMG.format(i) for i in [
        "1554568218-0f1715e72254", "1560769629-975ec94e6a86", "1550246140-29f40b909e5a",
    ]],
    "swimwear": [IMG.format(i) for i in [
        "1618932260643-eee4a2f652a6",
    ]],
    "shoes": [IMG.format(i) for i in [
        "1560769629-975ec94e6a86", "1544441893-675973e31985",
    ]],
    "accessories": [IMG.format(i) for i in [
        "1509941943102-10c232535736",
    ]],
    "dresses": [IMG.format(i) for i in [
        "1515372039744-b8f02a3ae446", "1571908599407-cdb918ed83bf",
    ]],
    "skirts": [IMG.format(i) for i in [
        "1618932260643-eee4a2f652a6", "1591195853828-11db59a44f6b",
    ]],
}
FALLBACK_IMAGE = IMG.format("1445205170230-053b83016050")


def pick_image(category_slug: str, idx: int) -> str:
    pool = IMAGE_POOL.get(category_slug) or [FALLBACK_IMAGE]
    return pool[idx % len(pool)]


CATEGORY_DEFS = [
    dict(slug="tshirts", name="T-Shirts", noun="Tee",
         materials=["100% organic cotton", "Pima cotton jersey", "cotton-modal blend"],
         price=(28, 48), size_type="clothing",
         adjectives=["Essential", "Relaxed", "Classic Crew", "Cropped", "Oversized"]),
    dict(slug="shirts", name="Shirts", noun="Shirt",
         materials=["brushed cotton flannel", "cotton poplin", "linen-cotton blend"],
         price=(58, 98), size_type="clothing",
         adjectives=["Tailored", "Everyday", "Button-Down", "Relaxed-Fit", "Weekend"]),
    dict(slug="hoodies", name="Hoodies", noun="Hoodie",
         materials=["fleece-back cotton", "organic cotton terry"],
         price=(68, 110), size_type="clothing",
         adjectives=["Signature", "Heavyweight", "Cropped", "Everyday"]),
    dict(slug="sweaters", name="Sweaters", noun="Sweater",
         materials=["merino wool", "cotton-cashmere blend", "chunky knit wool"],
         price=(78, 140), size_type="clothing",
         adjectives=["Fisherman", "Ribbed", "Fine-Knit", "Turtleneck"]),
    dict(slug="jackets", name="Jackets", noun="Jacket",
         materials=["full-grain leather", "waxed cotton canvas", "quilted recycled nylon"],
         price=(120, 220), size_type="clothing",
         adjectives=["Bomber", "Moto", "Field", "Quilted", "Utility"]),
    dict(slug="coats", name="Coats", noun="Coat",
         materials=["wool-blend melton", "shearling-lined suede", "technical waterproof shell"],
         price=(180, 320), size_type="clothing",
         adjectives=["Tailored Wool", "Long", "Shearling", "Storm"]),
    dict(slug="jeans", name="Jeans", noun="Jean",
         materials=["stretch selvedge denim", "rigid organic denim"],
         price=(78, 128), size_type="clothing",
         adjectives=["Slim-Fit", "Straight-Leg", "Relaxed", "High-Rise"]),
    dict(slug="trousers", name="Trousers", noun="Trouser",
         materials=["Italian wool blend", "stretch cotton twill"],
         price=(68, 120), size_type="clothing",
         adjectives=["Tailored", "Pleated", "Slim", "Wide-Leg"]),
    dict(slug="shorts", name="Shorts", noun="Short",
         materials=["cotton twill", "stretch chino"],
         price=(48, 78), size_type="clothing",
         adjectives=["Tailored", "Drawstring", "Classic"]),
    dict(slug="activewear", name="Activewear", noun="Performance Tee",
         materials=["moisture-wicking polyester blend", "brushed technical knit"],
         price=(48, 98), size_type="clothing",
         adjectives=["Training", "Run", "Studio", "Performance"]),
    dict(slug="swimwear", name="Swimwear", noun="Swim Short",
         materials=["quick-dry recycled nylon"],
         price=(48, 88), size_type="clothing",
         adjectives=["Resort", "Classic", "Printed"]),
    dict(slug="shoes", name="Shoes", noun="Sneaker",
         materials=["full-grain leather", "knit mesh upper"],
         price=(98, 190), size_type="shoes",
         adjectives=["Court", "Trail", "Everyday", "Minimalist"]),
    dict(slug="accessories", name="Accessories", noun="Accessory",
         materials=["Italian leather", "brushed stainless steel", "merino wool"],
         price=(38, 150), size_type="accessory",
         adjectives=["Signature", "Classic", "Woven"]),
    dict(slug="dresses", name="Dresses", noun="Dress",
         materials=["silk crepe", "cotton poplin", "stretch jersey", "satin"],
         price=(88, 220), size_type="clothing",
         adjectives=["Wrap", "Slip", "Midi", "Off-Shoulder", "Tailored"]),
    dict(slug="skirts", name="Skirts", noun="Skirt",
         materials=["wool-blend", "cotton twill", "satin"],
         price=(68, 110), size_type="clothing",
         adjectives=["A-Line", "Pleated", "Midi", "Wrap"]),
]

OCCASIONS = ["casual", "date-night", "pool-party", "business-casual", "streetwear",
             "minimal", "all-black", "vacation", "wedding", "party", "active", "formal"]
SEASONS = ["summer", "winter", "spring", "fall"]
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
]


def make_description(name: str, brand: str, material: str, occasion: str) -> str:
    template = random.choice(DESCRIPTION_TEMPLATES)
    return template.format(name=name, brand=brand, material=material, occasion=occasion)


def make_short_description(cat_name: str, material: str) -> str:
    return f"A refined {cat_name.lower()[:-1] if cat_name.endswith('s') else cat_name.lower()} in {material}."


def get_or_create_category(db: Session, slug: str, name: str) -> Category:
    existing = db.scalar(select(Category).where(Category.slug == slug))
    if existing:
        return existing
    category = Category(slug=slug, name=name, description=f"Shop {name.lower()} at Veloura.")
    db.add(category)
    db.flush()
    return category


def build_products() -> list[dict]:
    products: list[dict] = []
    brand_cycle = iter(BRANDS * 10)

    for cat in CATEGORY_DEFS:
        genders = ["women"] if cat["slug"] in ("dresses", "skirts") else ["men", "women"]
        per_gender = 5 if cat["slug"] in ("dresses",) else (4 if cat["slug"] == "skirts" else 2)

        for gender in genders:
            for i in range(per_gender):
                brand = next(brand_cycle)
                adjective = cat["adjectives"][i % len(cat["adjectives"])]
                material = cat["materials"][i % len(cat["materials"])]
                name = f"{adjective} {cat['noun']}"
                occasion = random.choice(OCCASIONS)
                season = random.choice(SEASONS)
                style = random.choice([s for s in STYLES])

                base_price = round(random.uniform(*cat["price"]), 2)
                on_sale = random.random() < 0.25
                sale_price = round(base_price * 0.8, 2) if on_sale else None

                size_list = {
                    "clothing": CLOTHING_SIZES,
                    "shoes": SHOE_SIZES,
                    "accessory": ONE_SIZE,
                }[cat["size_type"]]

                num_colors = 2 if cat["size_type"] == "accessory" else random.choice([2, 3])
                colors = random.sample(COLORS, k=num_colors)

                occasion_tags = list({occasion, random.choice(OCCASIONS)})
                style_tags = list({style, random.choice(STYLES)})
                season_tags = [season] if cat["slug"] not in ("coats", "sweaters", "swimwear") else (
                    ["winter", "fall"] if cat["slug"] in ("coats", "sweaters") else ["summer"]
                )

                variants = []
                for c_idx, (color_name, color_hex) in enumerate(colors):
                    sizes_for_color = size_list if cat["size_type"] != "accessory" else ONE_SIZE
                    for size in sizes_for_color:
                        sku_raw = f"{cat['slug'][:3].upper()}-{gender[:1].upper()}{i}{c_idx}-{size}"
                        sku = sku_raw.replace(" ", "")
                        variants.append(dict(
                            sku=sku,
                            size=size,
                            color_name=color_name,
                            color_hex=color_hex,
                            inventory_quantity=random.choice([0, 4, 8, 12, 20, 35]),
                            image_url=pick_image(cat["slug"], i + c_idx),
                        ))

                products.append(dict(
                    name=name,
                    brand=brand,
                    gender=gender,
                    category_slug=cat["slug"],
                    category_name=cat["name"],
                    base_price=base_price,
                    sale_price=sale_price,
                    material=material.capitalize(),
                    care_instructions="Machine wash cold, tumble dry low, do not bleach.",
                    occasion_tags=occasion_tags,
                    style_tags=style_tags,
                    season_tags=season_tags,
                    is_featured=random.random() < 0.2,
                    description=make_description(name, brand, material, occasion.replace("-", " ")),
                    short_description=make_short_description(cat["name"], material),
                    variants=variants,
                ))
    return products


def seed_products(db: Session) -> list[Product]:
    categories = {
        cat["slug"]: get_or_create_category(db, cat["slug"], cat["name"]) for cat in CATEGORY_DEFS
    }
    db.commit()

    created: list[Product] = []
    for data in build_products():
        slug = slugify(f"{data['brand']} {data['name']} {data['gender']}")
        existing = db.scalar(select(Product).where(Product.slug == slug))
        if existing:
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
    return created


def seed_users(db: Session) -> tuple[User, User]:
    admin = db.scalar(select(User).where(User.email == "admin@veloura.com"))
    if not admin:
        admin = User(
            email="admin@veloura.com",
            hashed_password=hash_password("AdminPass123!"),
            full_name="Veloura Admin",
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
            full_name="Ava Customer",
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
                is_default=True,
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

        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

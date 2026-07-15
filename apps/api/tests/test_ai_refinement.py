import uuid

from veloura_api.ai.refinement import RefinementAction, apply_refinement, detect_refinement
from veloura_api.models.category import Category
from veloura_api.models.product import Gender, Product, ProductVariant


def _make_product(
    *, name, brand, category_slug, base_price, style_tags, colors, gender=Gender.UNISEX
):
    category = Category(id=uuid.uuid4(), slug=category_slug, name=category_slug.title())
    product = Product(
        id=uuid.uuid4(),
        slug=name.lower().replace(" ", "-"),
        name=name,
        brand=brand,
        description="Test product.",
        short_description="Test.",
        gender=gender,
        base_price=base_price,
        material="Cotton",
        care_instructions="Wash cold.",
        occasion_tags=[],
        style_tags=style_tags,
        season_tags=[],
        is_active=True,
    )
    product.category = category
    product.variants = [
        ProductVariant(
            id=uuid.uuid4(),
            sku=f"SKU-{color}-{name}",
            size="M",
            color_name=color,
            color_hex="#000000",
            inventory_quantity=10,
            image_url="https://example.com/img.jpg",
        )
        for color in colors
    ]
    return product


def test_detect_refinement_cheaper():
    assert detect_refinement("Can you make it cheaper?").action == RefinementAction.CHEAPER
    assert detect_refinement("I want something less expensive").action == RefinementAction.CHEAPER


def test_detect_refinement_formal_and_casual():
    assert detect_refinement("Make it more formal please").action == RefinementAction.MORE_FORMAL
    assert detect_refinement("Can you make it more casual?").action == RefinementAction.MORE_CASUAL


def test_detect_refinement_color():
    intent = detect_refinement("Change the color to black")
    assert intent.action == RefinementAction.CHANGE_COLOR
    assert intent.color == "black"


def test_detect_refinement_replace_item():
    intent = detect_refinement("Can you replace the shoes?")
    assert intent.action == RefinementAction.REPLACE_ITEM
    assert intent.category_hint == "shoes"


def test_detect_refinement_returns_none_for_unrelated_message():
    assert detect_refinement("I need an outfit for a beach wedding") is None


def test_apply_refinement_cheaper_swaps_most_expensive_item():
    expensive_jacket = _make_product(
        name="Expensive Jacket", brand="A", category_slug="jackets", base_price=300,
        style_tags=["casual"], colors=["Black"],
    )
    cheap_jacket = _make_product(
        name="Cheap Jacket", brand="B", category_slug="jackets", base_price=100,
        style_tags=["casual"], colors=["Black"],
    )
    tee = _make_product(
        name="Basic Tee", brand="C", category_slug="tshirts", base_price=40,
        style_tags=["casual"], colors=["White"],
    )
    current_items = [(expensive_jacket, expensive_jacket.variants[0]), (tee, tee.variants[0])]
    candidates = [expensive_jacket, cheap_jacket, tee]

    result = apply_refinement(
        detect_refinement("make it cheaper"), current_items, candidates
    )
    assert result is not None
    products_in_result = {p.id for p, _, _ in result}
    assert cheap_jacket.id in products_in_result
    assert expensive_jacket.id not in products_in_result
    new_total = sum(p.effective_price for p, _, _ in result)
    old_total = sum(p.effective_price for p, _ in current_items)
    assert new_total < old_total


def test_apply_refinement_change_color_finds_same_product_variant():
    tee = _make_product(
        name="Basic Tee", brand="C", category_slug="tshirts", base_price=40,
        style_tags=["casual"], colors=["White", "Black"],
    )
    current_items = [(tee, tee.variants[0])]  # White variant
    result = apply_refinement(detect_refinement("change the color to black"), current_items, [tee])
    assert result is not None
    product, variant, _ = result[0]
    assert product.id == tee.id
    assert variant.color_name == "Black"


def test_apply_refinement_change_color_falls_back_to_alternative_product():
    tee_white_only = _make_product(
        name="White Tee", brand="C", category_slug="tshirts", base_price=40,
        style_tags=["casual"], colors=["White"],
    )
    tee_black = _make_product(
        name="Black Tee", brand="D", category_slug="tshirts", base_price=42,
        style_tags=["casual"], colors=["Black"],
    )
    current_items = [(tee_white_only, tee_white_only.variants[0])]
    candidates = [tee_white_only, tee_black]
    result = apply_refinement(
        detect_refinement("change the color to black"), current_items, candidates
    )
    assert result is not None
    product, variant, _ = result[0]
    assert product.id == tee_black.id
    assert variant.color_name == "Black"


def test_apply_refinement_replace_item_swaps_same_category():
    shoe_a = _make_product(
        name="Shoe A", brand="A", category_slug="shoes", base_price=100,
        style_tags=["casual"], colors=["Black"],
    )
    shoe_b = _make_product(
        name="Shoe B", brand="B", category_slug="shoes", base_price=120,
        style_tags=["casual"], colors=["White"],
    )
    current_items = [(shoe_a, shoe_a.variants[0])]
    result = apply_refinement(
        detect_refinement("replace the shoes"), current_items, [shoe_a, shoe_b]
    )
    assert result is not None
    product, _, _ = result[0]
    assert product.id == shoe_b.id


def test_apply_refinement_more_formal_prefers_formal_tagged_alternative():
    casual_trousers = _make_product(
        name="Casual Trousers", brand="A", category_slug="trousers", base_price=80,
        style_tags=["casual"], colors=["Navy"],
    )
    formal_trousers = _make_product(
        name="Formal Trousers", brand="B", category_slug="trousers", base_price=90,
        style_tags=["formal"], colors=["Navy"],
    )
    current_items = [(casual_trousers, casual_trousers.variants[0])]
    result = apply_refinement(
        detect_refinement("make it more formal"), current_items, [casual_trousers, formal_trousers]
    )
    assert result is not None
    product, _, _ = result[0]
    assert product.id == formal_trousers.id


def test_apply_refinement_returns_none_when_no_alternative_exists():
    only_jacket = _make_product(
        name="Only Jacket", brand="A", category_slug="jackets", base_price=150,
        style_tags=["casual"], colors=["Black"],
    )
    current_items = [(only_jacket, only_jacket.variants[0])]
    result = apply_refinement(detect_refinement("replace the jacket"), current_items, [only_jacket])
    assert result is None

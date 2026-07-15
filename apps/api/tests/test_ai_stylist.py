import uuid

from veloura_api.ai.outfit_generation import (
    OutfitItemSuggestion,
    OutfitSuggestion,
    StylistLLMResponse,
    generate_outfits,
)
from veloura_api.ai.preferences import extract_preferences
from veloura_api.ai.retrieval import get_candidate_products


def test_extract_preferences_parses_occasion_budget_and_colors():
    prefs = extract_preferences("I am going to a pool party. Suggest an outfit under $150.")
    assert prefs.occasion == "pool party"
    assert prefs.budget == 150.0


def test_extract_preferences_parses_all_black_and_date_night():
    prefs = extract_preferences("I am going on a late-night date. Suggest an all-black outfit.")
    assert prefs.occasion == "date night"
    assert "black" in prefs.preferred_colors


def test_extract_preferences_defaults_when_nothing_specific_said():
    prefs = extract_preferences("Surprise me!")
    assert prefs.occasion == "everyday"
    assert prefs.budget is None


def test_candidate_retrieval_only_returns_active_in_stock_products(db_session, seed_catalog):
    prefs = extract_preferences("Something casual for summer")
    candidates = get_candidate_products(db_session, prefs)

    candidate_ids = {p.id for p in candidates}
    assert seed_catalog["product"].id in candidate_ids
    assert seed_catalog["inactive_product"].id not in candidate_ids

    # Only the in-stock variant should ever be offered as a candidate.
    matched_product = next(p for p in candidates if p.id == seed_catalog["product"].id)
    in_stock_variant_ids = {v.id for v in matched_product.variants if v.inventory_quantity > 0}
    assert seed_catalog["variant_in_stock"].id in in_stock_variant_ids
    assert seed_catalog["variant_out_of_stock"].id not in in_stock_variant_ids


def test_candidate_retrieval_respects_budget(db_session, seed_catalog):
    prefs = extract_preferences("Something nice under $10")
    candidates = get_candidate_products(db_session, prefs)
    # Essential Tee is $40, above the $10 budget, so it should be excluded.
    assert seed_catalog["product"].id not in {p.id for p in candidates}


def test_generate_outfits_never_hallucinates_products(db_session, seed_catalog):
    """Even if something upstream produced a fabricated product/variant ID, the
    validation layer must strip it before it reaches the API response."""
    prefs = extract_preferences("Casual outfit")
    candidates = get_candidate_products(db_session, prefs)

    real_variant = seed_catalog["variant_in_stock"]
    real_product = seed_catalog["product"]

    fake_response = StylistLLMResponse(
        summary="Test",
        outfits=[
            OutfitSuggestion(
                name="Fabricated Outfit",
                explanation="Contains a hallucinated item that must be stripped.",
                items=[
                    OutfitItemSuggestion(
                        product_id=str(real_product.id),
                        variant_id=str(real_variant.id),
                        reason="Real item.",
                    ),
                    OutfitItemSuggestion(
                        product_id=str(uuid.uuid4()),
                        variant_id=str(uuid.uuid4()),
                        reason="This product does not exist in the catalog.",
                    ),
                ],
            )
        ],
        follow_up_suggestions=[],
    )

    from veloura_api.ai.outfit_generation import _validate_and_price

    validated = _validate_and_price(fake_response, candidates, prefs)
    assert len(validated.outfits) == 1
    assert len(validated.outfits[0].items) == 1
    assert validated.outfits[0].items[0].product_id == str(real_product.id)


def test_generate_outfits_heuristic_respects_budget(db_session, seed_catalog):
    prefs = extract_preferences("Casual outfit for summer under $30")
    candidates = get_candidate_products(db_session, prefs)
    result = generate_outfits(candidates, prefs)
    for outfit in result.outfits:
        total = sum(
            next(p for p in candidates if str(p.id) == item.product_id).effective_price
            for item in outfit.items
        )
        assert total <= 30 * 1.05 or len(result.outfits) == 0


def test_ai_stylist_recommend_endpoint_returns_real_products(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    response = client.post(
        "/api/ai-stylist/recommend",
        headers=headers,
        json={"message": "I need something casual for summer."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]

    valid_product_ids = {str(seed_catalog["product"].id)}
    for outfit in body["outfits"]:
        for item in outfit["items"]:
            assert item["product_id"] in valid_product_ids
            assert item["variant_id"] == str(seed_catalog["variant_in_stock"].id)


def test_ai_stylist_refinement_changes_color_in_same_session(client, auth_headers, db_session, seed_catalog):
    from veloura_api.models.product import Product, ProductVariant

    product = Product(
        slug="two-tone-tee",
        name="Two-Tone Tee",
        brand="Test Brand",
        description="A tee available in two colors for refinement testing.",
        short_description="Two colors.",
        gender=seed_catalog["product"].gender,
        category_id=seed_catalog["category"].id,
        base_price=45.00,
        material="Cotton",
        care_instructions="Wash cold.",
        occasion_tags=["casual"],
        style_tags=["casual"],
        season_tags=["summer"],
        is_active=True,
    )
    product.variants = [
        ProductVariant(
            sku="TT-BLACK", size="M", color_name="Black", color_hex="#111111",
            inventory_quantity=10, image_url="https://example.com/black.jpg",
        ),
        ProductVariant(
            sku="TT-RED", size="M", color_name="Red", color_hex="#B33A3A",
            inventory_quantity=10, image_url="https://example.com/red.jpg",
        ),
    ]
    db_session.add(product)
    db_session.commit()

    headers, _ = auth_headers
    first = client.post(
        "/api/ai-stylist/recommend",
        headers=headers,
        json={"message": "Casual outfit, nothing too expensive"},
    )
    assert first.status_code == 200
    session_id = first.json()["session_id"]
    assert len(first.json()["outfits"]) >= 1

    refine = client.post(
        "/api/ai-stylist/recommend",
        headers=headers,
        json={"message": "Change the color to red", "session_id": session_id},
    )
    assert refine.status_code == 200
    body = refine.json()
    assert len(body["outfits"]) == 1
    colors = {item["color_name"] for item in body["outfits"][0]["items"]}
    assert "Red" in colors

    detail = client.get(f"/api/ai-stylist/sessions/{session_id}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 4  # 2 user + 2 assistant turns


def test_ai_stylist_uses_saved_style_profile_budget(client, auth_headers, seed_catalog, second_product):
    headers, _ = auth_headers
    client.put("/api/account/style-profile", headers=headers, json={"budget_max": 50})

    response = client.post(
        "/api/ai-stylist/recommend", headers=headers, json={"message": "Something casual for everyday"}
    )
    assert response.status_code == 200
    for outfit in response.json()["outfits"]:
        for item in outfit["items"]:
            assert item["price"] <= 50


def test_ai_stylist_builds_outfit_around_cart_item(client, auth_headers, seed_catalog, second_product):
    headers, _ = auth_headers
    client.post(
        "/api/cart/items",
        headers=headers,
        json={"variant_id": str(second_product.variants[0].id), "quantity": 1},
    )

    response = client.post(
        "/api/ai-stylist/recommend",
        headers=headers,
        json={"message": "Build an outfit around the jacket in my cart"},
    )
    assert response.status_code == 200
    body = response.json()
    all_product_ids = {item["product_id"] for outfit in body["outfits"] for item in outfit["items"]}
    assert str(second_product.id) in all_product_ids


def test_ai_stylist_sessions_list_and_detail(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    recommend_response = client.post(
        "/api/ai-stylist/recommend", headers=headers, json={"message": "Casual summer look"}
    )
    session_id = recommend_response.json()["session_id"]

    sessions_response = client.get("/api/ai-stylist/sessions", headers=headers)
    assert sessions_response.status_code == 200
    assert any(s["id"] == session_id for s in sessions_response.json())

    detail_response = client.get(f"/api/ai-stylist/sessions/{session_id}", headers=headers)
    assert detail_response.status_code == 200
    assert len(detail_response.json()["messages"]) == 2  # user + assistant

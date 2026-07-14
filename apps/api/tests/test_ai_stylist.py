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

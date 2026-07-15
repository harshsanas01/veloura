VALID_ADDRESS = {
    "full_name": "Ava Customer",
    "line1": "1 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "United States",
    "phone": "+15551234567",
}


def test_trending_falls_back_to_featured_when_no_sales(client, seed_catalog):
    response = client.get("/api/recommendations/trending")
    assert response.status_code == 200
    slugs = [p["slug"] for p in response.json()]
    assert "test-essential-tee" in slugs


def test_trending_prioritizes_recently_sold_products(client, auth_headers, seed_catalog, second_product):
    headers, _ = auth_headers
    client.post(
        "/api/cart/items",
        headers=headers,
        json={"variant_id": str(second_product.variants[0].id), "quantity": 1},
    )
    client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})

    response = client.get("/api/recommendations/trending", params={"gender": "men"})
    assert response.status_code == 200
    slugs = [p["slug"] for p in response.json()]
    assert slugs[0] == "test-moto-jacket"


def test_also_bought_returns_co_purchased_products(client, auth_headers, seed_catalog, second_product):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    client.post("/api/cart/items", headers=headers, json={"variant_id": str(variant.id), "quantity": 1})
    client.post(
        "/api/cart/items",
        headers=headers,
        json={"variant_id": str(second_product.variants[0].id), "quantity": 1},
    )
    client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})

    response = client.get(f"/api/products/{seed_catalog['product'].id}/also-bought")
    assert response.status_code == 200
    slugs = [p["slug"] for p in response.json()]
    assert "test-moto-jacket" in slugs


def test_complete_the_look_returns_complementary_categories(client, second_product):
    response = client.get(f"/api/products/{second_product.id}/complete-the-look")
    assert response.status_code == 200
    # second_product is a men's jacket ("layer" slot) - results should never
    # include another jacket (same slot) and should stay in men's/unisex gender.
    for item in response.json():
        assert item["category_slug"] != "jackets"
        assert item["gender"] in ("men", "unisex")

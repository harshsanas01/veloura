def test_list_products_returns_only_active(client, seed_catalog):
    response = client.get("/api/products")
    assert response.status_code == 200
    body = response.json()
    slugs = [p["slug"] for p in body["items"]]
    assert "test-essential-tee" in slugs
    assert "test-inactive-item" not in slugs


def test_list_products_filter_by_category(client, seed_catalog):
    response = client.get("/api/products", params={"category": "tshirts"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_products_filter_by_missing_category_returns_empty(client, seed_catalog):
    response = client.get("/api/products", params={"category": "shoes"})
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_list_products_price_filter(client, seed_catalog):
    response = client.get("/api/products", params={"min_price": 100})
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_get_product_detail_by_slug(client, seed_catalog):
    response = client.get("/api/products/test-essential-tee")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Essential Tee"
    assert len(body["variants"]) == 2
    assert "Black" in [c["name"] for c in body["available_colors"]]


def test_get_product_detail_404_for_inactive(client, seed_catalog):
    response = client.get("/api/products/test-inactive-item")
    assert response.status_code == 404


def test_get_product_detail_404_for_unknown_slug(client):
    response = client.get("/api/products/does-not-exist")
    assert response.status_code == 404


def test_list_products_filter_by_brand(client, second_product):
    response = client.get("/api/products", params={"brand": "Solstice Denim"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["slug"] == "test-moto-jacket"


def test_list_products_filter_by_material(client, second_product):
    response = client.get("/api/products", params={"material": "Waxed cotton canvas"})
    assert response.json()["total"] == 1


def test_list_products_filter_by_occasion(client, second_product):
    response = client.get("/api/products", params={"occasion": "streetwear"})
    assert response.json()["total"] == 1
    response = client.get("/api/products", params={"occasion": "wedding"})
    assert response.json()["total"] == 0


def test_list_products_filter_by_season(client, second_product):
    response = client.get("/api/products", params={"season": "winter"})
    assert response.json()["total"] == 1


def test_list_products_sale_only_filter(client, second_product):
    response = client.get("/api/products", params={"sale_only": True})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["sale_price"] is not None


def test_list_products_in_stock_only_filter(client, second_product, seed_catalog):
    # the out-of-stock variant belongs to the shared essential tee; with
    # in_stock_only both products should still appear since each has at least
    # one in-stock variant.
    response = client.get("/api/products", params={"in_stock_only": True})
    assert response.json()["total"] == 2


def test_search_matches_material_and_tags(client, second_product):
    response = client.get("/api/products", params={"q": "waxed cotton"})
    assert response.json()["total"] == 1

    response = client.get("/api/products", params={"q": "streetwear"})
    assert response.json()["total"] == 1


def test_search_matches_variant_color(client, second_product):
    response = client.get("/api/products", params={"q": "charcoal"})
    assert response.json()["total"] == 1


def test_sort_by_biggest_discount(client, second_product):
    response = client.get("/api/products", params={"sort": "biggest_discount"})
    body = response.json()
    assert body["items"][0]["slug"] == "test-moto-jacket"


def test_facets_endpoint_returns_distinct_values(client, second_product):
    response = client.get("/api/products/facets")
    assert response.status_code == 200
    body = response.json()
    assert "Solstice Denim" in body["brands"]
    assert "Waxed cotton canvas" in body["materials"]
    assert "streetwear" in body["occasions"]
    assert "winter" in body["seasons"]
    assert body["max_price"] >= 150

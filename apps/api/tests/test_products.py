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

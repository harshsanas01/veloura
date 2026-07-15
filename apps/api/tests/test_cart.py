def test_add_item_to_cart(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant_id = str(seed_catalog["variant_in_stock"].id)

    response = client.post("/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": 2})
    assert response.status_code == 201
    body = response.json()
    assert body["item_count"] == 2
    assert body["items"][0]["quantity"] == 2


def test_update_cart_item_quantity(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant_id = str(seed_catalog["variant_in_stock"].id)

    add_response = client.post(
        "/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": 1}
    )
    item_id = add_response.json()["items"][0]["id"]

    update_response = client.patch(f"/api/cart/items/{item_id}", headers=headers, json={"quantity": 5})
    assert update_response.status_code == 200
    assert update_response.json()["items"][0]["quantity"] == 5


def test_add_item_beyond_inventory_returns_409(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant_id = str(seed_catalog["variant_in_stock"].id)  # inventory_quantity = 10

    response = client.post(
        "/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": 15}
    )
    assert response.status_code == 409


def test_add_out_of_stock_variant_returns_409(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant_id = str(seed_catalog["variant_out_of_stock"].id)

    response = client.post("/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": 1})
    assert response.status_code == 409


def test_remove_cart_item(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant_id = str(seed_catalog["variant_in_stock"].id)

    add_response = client.post(
        "/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": 1}
    )
    item_id = add_response.json()["items"][0]["id"]

    remove_response = client.delete(f"/api/cart/items/{item_id}", headers=headers)
    assert remove_response.status_code == 200
    assert remove_response.json()["items"] == []


def test_cart_requires_authentication(client):
    response = client.get("/api/cart")
    assert response.status_code == 401

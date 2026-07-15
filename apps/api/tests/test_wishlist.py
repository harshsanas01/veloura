def test_add_and_list_wishlist_item(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)

    response = client.post("/api/wishlist/items", headers=headers, json={"product_id": product_id})
    assert response.status_code == 201
    assert len(response.json()["items"]) == 1

    list_response = client.get("/api/wishlist", headers=headers)
    assert list_response.json()["items"][0]["product_id"] == product_id


def test_adding_same_item_twice_is_idempotent(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)

    client.post("/api/wishlist/items", headers=headers, json={"product_id": product_id})
    response = client.post("/api/wishlist/items", headers=headers, json={"product_id": product_id})
    assert len(response.json()["items"]) == 1


def test_remove_wishlist_item(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)

    client.post("/api/wishlist/items", headers=headers, json={"product_id": product_id})
    response = client.delete(f"/api/wishlist/items/{product_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_wishlist_item_reports_sale_status(client, auth_headers, second_product):
    headers, _ = auth_headers
    product_id = str(second_product.id)

    response = client.post("/api/wishlist/items", headers=headers, json={"product_id": product_id})
    item = response.json()["items"][0]
    assert item["on_sale"] is True
    assert item["sale_price"] == 150.0


def test_move_wishlist_item_to_cart(client, auth_headers, second_product):
    headers, _ = auth_headers
    product_id = str(second_product.id)
    variant_id = str(second_product.variants[0].id)

    client.post("/api/wishlist/items", headers=headers, json={"product_id": product_id})
    response = client.post(
        f"/api/wishlist/items/{product_id}/move-to-cart",
        headers=headers,
        json={"variant_id": variant_id, "quantity": 1},
    )
    assert response.status_code == 200
    assert response.json()["items"] == []

    cart = client.get("/api/cart", headers=headers).json()
    assert cart["items"][0]["variant"]["id"] == variant_id


def test_move_wishlist_item_to_cart_rejects_mismatched_variant(
    client, auth_headers, seed_catalog, second_product
):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    wrong_variant_id = str(second_product.variants[0].id)

    client.post("/api/wishlist/items", headers=headers, json={"product_id": product_id})
    response = client.post(
        f"/api/wishlist/items/{product_id}/move-to-cart",
        headers=headers,
        json={"variant_id": wrong_variant_id, "quantity": 1},
    )
    assert response.status_code == 400

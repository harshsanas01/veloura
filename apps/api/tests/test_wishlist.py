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

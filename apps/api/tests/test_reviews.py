VALID_ADDRESS = {
    "full_name": "Ava Customer",
    "line1": "1 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "United States",
    "phone": "+15551234567",
}


def test_unauthenticated_cannot_post_review(client, seed_catalog):
    response = client.post(
        f"/api/products/{seed_catalog['product'].id}/reviews",
        json={"rating": 5, "title": "Great", "body": "Loved it."},
    )
    assert response.status_code == 401


def test_create_and_list_review(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)

    response = client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 4, "title": "Pretty good", "body": "Fits well, nice fabric."},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 4
    assert body["is_verified_purchase"] is False
    assert body["is_mine"] is True

    list_response = client.get(f"/api/products/{product_id}/reviews")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total"] == 1
    assert listed["average_rating"] == 4.0
    assert listed["distribution"]["four"] == 1


def test_duplicate_review_rejected(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    payload = {"rating": 5, "title": "Love it", "body": "Great product."}

    first = client.post(f"/api/products/{product_id}/reviews", headers=headers, json=payload)
    assert first.status_code == 201

    second = client.post(f"/api/products/{product_id}/reviews", headers=headers, json=payload)
    assert second.status_code == 409


def test_verified_purchase_badge_set_after_order(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    client.post("/api/cart/items", headers=headers, json={"variant_id": str(variant.id), "quantity": 1})
    client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})

    product_id = str(seed_catalog["product"].id)
    response = client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 5, "title": "As expected", "body": "Exactly what I ordered."},
    )
    assert response.status_code == 201
    assert response.json()["is_verified_purchase"] is True


def test_user_can_edit_and_delete_own_review(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    review = client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 3, "title": "Okay", "body": "It's fine."},
    ).json()

    update = client.patch(
        f"/api/reviews/{review['id']}", headers=headers, json={"rating": 5, "title": "Actually great"}
    )
    assert update.status_code == 200
    assert update.json()["rating"] == 5
    assert update.json()["title"] == "Actually great"

    delete = client.delete(f"/api/reviews/{review['id']}", headers=headers)
    assert delete.status_code == 204

    listing = client.get(f"/api/products/{product_id}/reviews").json()
    assert listing["total"] == 0


def test_cannot_edit_or_delete_other_users_review(client, auth_headers, register_user, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    review = client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 4, "title": "Nice", "body": "Good quality."},
    ).json()

    other = register_user(email="otherreviewer@example.com")
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    update = client.patch(
        f"/api/reviews/{review['id']}", headers=other_headers, json={"rating": 1}
    )
    assert update.status_code == 404

    delete = client.delete(f"/api/reviews/{review['id']}", headers=other_headers)
    assert delete.status_code == 404


def test_toggle_helpful_vote(client, auth_headers, register_user, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    review = client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 5, "title": "Perfect", "body": "No notes."},
    ).json()

    voter = register_user(email="helpfulvoter@example.com")
    voter_headers = {"Authorization": f"Bearer {voter['access_token']}"}

    first_vote = client.post(f"/api/reviews/{review['id']}/helpful", headers=voter_headers)
    assert first_vote.status_code == 200
    assert first_vote.json()["helpful_count"] == 1
    assert first_vote.json()["helpful_by_me"] is True

    second_vote = client.post(f"/api/reviews/{review['id']}/helpful", headers=voter_headers)
    assert second_vote.json()["helpful_count"] == 0
    assert second_vote.json()["helpful_by_me"] is False


def test_reviews_sorted_by_highest_and_lowest(client, auth_headers, register_user, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 2, "title": "Meh", "body": "Not for me."},
    )
    other = register_user(email="fivestarreviewer@example.com")
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    client.post(
        f"/api/products/{product_id}/reviews",
        headers=other_headers,
        json={"rating": 5, "title": "Amazing", "body": "Loved every bit."},
    )

    highest = client.get(f"/api/products/{product_id}/reviews", params={"sort": "highest"}).json()
    assert highest["items"][0]["rating"] == 5

    lowest = client.get(f"/api/products/{product_id}/reviews", params={"sort": "lowest"}).json()
    assert lowest["items"][0]["rating"] == 2


def test_admin_can_moderate_review(client, auth_headers, admin_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    review = client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 1, "title": "Spam", "body": "buy my stuff at spam-site.example"},
    ).json()

    response = client.patch(
        f"/api/admin/reviews/{review['id']}", headers=admin_headers, json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    listing = client.get(f"/api/products/{product_id}/reviews").json()
    assert listing["total"] == 0

    admin_list = client.get("/api/admin/reviews", headers=admin_headers).json()
    assert any(r["id"] == review["id"] for r in admin_list)


def test_non_admin_cannot_moderate_review(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    product_id = str(seed_catalog["product"].id)
    review = client.post(
        f"/api/products/{product_id}/reviews",
        headers=headers,
        json={"rating": 3, "title": "Fine", "body": "It works."},
    ).json()

    response = client.patch(f"/api/admin/reviews/{review['id']}", headers=headers, json={"is_active": False})
    assert response.status_code == 403

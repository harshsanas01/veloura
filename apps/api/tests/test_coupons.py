VALID_ADDRESS = {
    "full_name": "Ava Customer",
    "line1": "1 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "United States",
    "phone": "+15551234567",
}


def _add_to_cart(client, headers, variant_id, quantity=1):
    return client.post(
        "/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": quantity}
    )


def test_apply_valid_coupon_computes_discount(client, auth_headers, seed_catalog, percent_coupon):
    headers, _ = auth_headers
    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))

    response = client.post("/api/cart/coupon", headers=headers, json={"code": "testpct10"})
    assert response.status_code == 200
    body = response.json()
    assert body["coupon_code"] == "TESTPCT10"
    assert body["discount_amount"] == 4.0  # 10% of $40


def test_apply_unknown_coupon_rejected(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))

    response = client.post("/api/cart/coupon", headers=headers, json={"code": "NOTREAL"})
    assert response.status_code == 400


def test_remove_coupon(client, auth_headers, seed_catalog, percent_coupon):
    headers, _ = auth_headers
    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))
    client.post("/api/cart/coupon", headers=headers, json={"code": "TESTPCT10"})

    response = client.delete("/api/cart/coupon", headers=headers)
    assert response.status_code == 200
    assert response.json()["coupon_code"] is None


def test_checkout_applies_coupon_and_records_redemption(client, auth_headers, seed_catalog, percent_coupon):
    headers, _ = auth_headers
    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))

    response = client.post(
        "/api/orders",
        headers=headers,
        json={"shipping_address": VALID_ADDRESS, "coupon_code": "TESTPCT10"},
    )
    assert response.status_code == 201
    order = response.json()
    assert order["discount_amount"] == 4.0
    assert order["subtotal"] == 40.0
    assert round(order["tax"], 2) == round(36.0 * 0.0825, 2)

    # Per-user limit isn't set on this coupon, but re-applying to a fresh cart
    # should still validate and compute correctly (no double-redemption bugs).
    second = client.post("/api/cart/coupon", headers=headers, json={"code": "TESTPCT10"})
    assert second.status_code == 400  # empty cart now, nothing to discount


def test_checkout_rejects_invalid_coupon_code(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))

    response = client.post(
        "/api/orders",
        headers=headers,
        json={"shipping_address": VALID_ADDRESS, "coupon_code": "NOTREAL"},
    )
    assert response.status_code == 400


def test_coupon_per_user_limit_enforced(client, auth_headers, seed_catalog, db_session):
    from veloura_api.models.coupon import Coupon, DiscountType

    coupon = Coupon(
        code="ONEUSE",
        discount_type=DiscountType.FIXED,
        discount_value=5,
        is_active=True,
        per_user_limit=1,
        applicable_categories=[],
        applicable_products=[],
    )
    db_session.add(coupon)
    db_session.commit()

    headers, _ = auth_headers
    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))
    first = client.post(
        "/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS, "coupon_code": "ONEUSE"}
    )
    assert first.status_code == 201

    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))
    second = client.post(
        "/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS, "coupon_code": "ONEUSE"}
    )
    assert second.status_code == 400


def test_coupon_min_order_value_enforced(client, auth_headers, seed_catalog, db_session):
    from veloura_api.models.coupon import Coupon, DiscountType

    coupon = Coupon(
        code="BIGORDER",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=15,
        is_active=True,
        min_order_value=500,
        applicable_categories=[],
        applicable_products=[],
    )
    db_session.add(coupon)
    db_session.commit()

    headers, _ = auth_headers
    _add_to_cart(client, headers, str(seed_catalog["variant_in_stock"].id))
    response = client.post("/api/cart/coupon", headers=headers, json={"code": "BIGORDER"})
    assert response.status_code == 400

import uuid

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


def test_checkout_creates_order_and_decrements_inventory(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=1)

    response = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})
    assert response.status_code == 201
    order = response.json()
    assert order["items"][0]["quantity"] == 1
    assert order["subtotal"] == 40.0  # 1 x $40.00
    assert order["shipping_cost"] == 7.99  # under $100 free-shipping threshold
    assert round(order["tax"], 2) == round(40.0 * 0.0825, 2)
    assert order["status"] == "paid"

    product_response = client.get("/api/products/test-essential-tee")
    updated_variant = next(v for v in product_response.json()["variants"] if v["id"] == str(variant.id))
    assert updated_variant["inventory_quantity"] == 9  # 10 - 1

    cart_response = client.get("/api/cart", headers=headers)
    assert cart_response.json()["items"] == []


def test_checkout_free_shipping_over_threshold(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=3)  # $120 subtotal

    response = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})
    assert response.json()["shipping_cost"] == 0.0


def test_checkout_fails_with_empty_cart(client, auth_headers):
    headers, _ = auth_headers
    response = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})
    assert response.status_code == 400


def test_checkout_prevents_overselling_inventory(client, auth_headers, seed_catalog, db_session):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=5)

    # Simulate inventory being sold out by another order between add-to-cart and checkout.
    variant.inventory_quantity = 2
    db_session.commit()

    response = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})
    assert response.status_code == 409


def test_list_orders_and_get_order_detail(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=1)
    create_response = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})
    order_id = create_response.json()["id"]

    list_response = client.get("/api/orders", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/orders/{order_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == order_id


def test_order_records_inventory_transaction_and_status_history(
    client, auth_headers, seed_catalog, db_session
):
    from veloura_api.models.inventory_transaction import InventoryChangeReason, InventoryTransaction
    from veloura_api.models.order_status_history import OrderStatusHistory

    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=2)

    response = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS})
    order_id = response.json()["id"]

    transactions = (
        db_session.query(InventoryTransaction).filter(InventoryTransaction.variant_id == variant.id).all()
    )
    assert len(transactions) == 1
    assert transactions[0].change_quantity == -2
    assert transactions[0].reason == InventoryChangeReason.ORDER_PLACED

    history = (
        db_session.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == uuid.UUID(order_id)).all()
    )
    assert len(history) == 1
    assert history[0].status.value == "paid"

    detail = client.get(f"/api/orders/{order_id}", headers=headers).json()
    assert detail["can_cancel"] is True
    assert len(detail["status_history"]) == 1


def test_customer_can_cancel_order_and_inventory_is_restored(client, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=2)
    order_id = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS}).json()[
        "id"
    ]

    response = client.post(f"/api/orders/{order_id}/cancel", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["can_cancel"] is False
    assert len(body["status_history"]) == 2

    product_response = client.get("/api/products/test-essential-tee")
    updated_variant = next(v for v in product_response.json()["variants"] if v["id"] == str(variant.id))
    assert updated_variant["inventory_quantity"] == 10  # fully restored


def test_cannot_cancel_shipped_order(client, auth_headers, admin_headers, seed_catalog):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=1)
    order_id = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS}).json()[
        "id"
    ]

    client.patch(f"/api/admin/orders/{order_id}/status", headers=admin_headers, json={"status": "shipped"})

    response = client.post(f"/api/orders/{order_id}/cancel", headers=headers)
    assert response.status_code == 409


def test_admin_cancelling_order_restores_inventory(client, auth_headers, admin_headers, seed_catalog):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=3)
    order_id = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS}).json()[
        "id"
    ]

    response = client.patch(
        f"/api/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "cancelled", "note": "Customer requested via support."},
    )
    assert response.status_code == 200

    product_response = client.get("/api/products/test-essential-tee")
    updated_variant = next(v for v in product_response.json()["variants"] if v["id"] == str(variant.id))
    assert updated_variant["inventory_quantity"] == 10


def test_cannot_view_another_users_order(client, auth_headers, seed_catalog, register_user):
    headers, _ = auth_headers
    variant = seed_catalog["variant_in_stock"]
    _add_to_cart(client, headers, str(variant.id), quantity=1)
    order_id = client.post("/api/orders", headers=headers, json={"shipping_address": VALID_ADDRESS}).json()[
        "id"
    ]

    other_user = register_user(email="other@example.com")
    other_headers = {"Authorization": f"Bearer {other_user['access_token']}"}
    response = client.get(f"/api/orders/{order_id}", headers=other_headers)
    assert response.status_code == 404

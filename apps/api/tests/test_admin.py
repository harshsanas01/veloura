def test_non_admin_cannot_access_admin_products(client, auth_headers):
    headers, _ = auth_headers
    response = client.get("/api/admin/products", headers=headers)
    assert response.status_code == 403


def test_unauthenticated_cannot_access_admin_products(client):
    response = client.get("/api/admin/products")
    assert response.status_code == 401


def test_admin_can_list_products(client, admin_headers, seed_catalog):
    response = client.get("/api/admin/products", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2  # active + inactive both visible to admin
    assert len(body["items"]) == 2


def test_admin_can_search_products(client, admin_headers, seed_catalog):
    response = client.get("/api/admin/products", headers=admin_headers, params={"q": "essential"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Essential Tee"


def test_admin_products_paginated(client, admin_headers, seed_catalog):
    response = client.get("/api/admin/products", headers=admin_headers, params={"page": 1, "page_size": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["total_pages"] == 2


def test_admin_can_create_product(client, admin_headers, seed_catalog):
    category_id = str(seed_catalog["category"].id)
    payload = {
        "name": "Admin Created Shirt",
        "brand": "Veloura Studio",
        "description": "A shirt created via the admin API for testing purposes.",
        "short_description": "Admin test shirt.",
        "gender": "men",
        "category_id": category_id,
        "base_price": 59.99,
        "material": "Cotton",
        "care_instructions": "Machine wash cold.",
        "occasion_tags": ["casual"],
        "style_tags": ["casual"],
        "season_tags": ["summer"],
        "is_featured": False,
        "is_active": True,
        "variants": [
            {
                "sku": "ADMIN-TEST-1",
                "size": "M",
                "color_name": "Navy",
                "color_hex": "#1B2A4A",
                "inventory_quantity": 5,
                "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800&q=80",
            }
        ],
    }
    response = client.post("/api/admin/products", headers=admin_headers, json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Admin Created Shirt"
    assert len(body["variants"]) == 1


def test_admin_can_update_variant_inventory(client, admin_headers, seed_catalog):
    variant_id = str(seed_catalog["variant_in_stock"].id)
    response = client.patch(
        f"/api/admin/variants/{variant_id}", headers=admin_headers, json={"inventory_quantity": 42}
    )
    assert response.status_code == 200
    assert response.json()["inventory_quantity"] == 42


def test_admin_can_deactivate_product(client, admin_headers, seed_catalog):
    product_id = str(seed_catalog["product"].id)
    response = client.patch(
        f"/api/admin/products/{product_id}", headers=admin_headers, json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_admin_can_delete_variant(client, admin_headers, seed_catalog):
    variant_id = str(seed_catalog["variant_out_of_stock"].id)
    response = client.delete(f"/api/admin/variants/{variant_id}", headers=admin_headers)
    assert response.status_code == 204


def test_admin_can_adjust_inventory_with_reason(client, admin_headers, seed_catalog):
    variant_id = str(seed_catalog["variant_in_stock"].id)
    response = client.post(
        f"/api/admin/variants/{variant_id}/adjust-inventory",
        headers=admin_headers,
        json={"delta": 5, "reason": "Received new stock shipment."},
    )
    assert response.status_code == 200
    assert response.json()["inventory_quantity"] == 15  # 10 + 5


def test_admin_inventory_adjustment_cannot_go_negative(client, admin_headers, seed_catalog):
    variant_id = str(seed_catalog["variant_in_stock"].id)
    response = client.post(
        f"/api/admin/variants/{variant_id}/adjust-inventory",
        headers=admin_headers,
        json={"delta": -999, "reason": "Testing negative floor."},
    )
    assert response.status_code == 400


def test_admin_inventory_adjustment_requires_reason(client, admin_headers, seed_catalog):
    variant_id = str(seed_catalog["variant_in_stock"].id)
    response = client.post(
        f"/api/admin/variants/{variant_id}/adjust-inventory",
        headers=admin_headers,
        json={"delta": 5, "reason": ""},
    )
    assert response.status_code == 422


def test_admin_dashboard_returns_metrics(client, admin_headers, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant_id = str(seed_catalog["variant_in_stock"].id)
    client.post("/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": 1})
    client.post(
        "/api/orders",
        headers=headers,
        json={
            "shipping_address": {
                "full_name": "Ava", "line1": "1 Main St", "city": "NYC", "state": "NY",
                "postal_code": "10001", "country": "US", "phone": "+15551234567",
            }
        },
    )

    response = client.get("/api/admin/dashboard", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_orders"] >= 1
    assert body["total_revenue"] > 0
    assert body["average_order_value"] > 0
    assert len(body["recent_orders"]) >= 1
    assert isinstance(body["best_selling_products"], list)
    assert isinstance(body["top_categories"], list)


def test_admin_can_list_customers(client, admin_headers, auth_headers):
    response = client.get("/api/admin/customers", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any("order_count" in c for c in body["items"])


def test_non_admin_cannot_access_dashboard_or_customers(client, auth_headers):
    headers, _ = auth_headers
    assert client.get("/api/admin/dashboard", headers=headers).status_code == 403
    assert client.get("/api/admin/customers", headers=headers).status_code == 403


def test_admin_coupon_crud(client, admin_headers):
    create = client.post(
        "/api/admin/coupons",
        headers=admin_headers,
        json={"code": "TESTCOUPON", "discount_type": "percentage", "discount_value": 15},
    )
    assert create.status_code == 201
    coupon_id = create.json()["id"]
    assert create.json()["code"] == "TESTCOUPON"
    assert create.json()["total_redemptions"] == 0

    duplicate = client.post(
        "/api/admin/coupons",
        headers=admin_headers,
        json={"code": "testcoupon", "discount_type": "fixed", "discount_value": 5},
    )
    assert duplicate.status_code == 409

    update = client.patch(
        f"/api/admin/coupons/{coupon_id}", headers=admin_headers, json={"is_active": False}
    )
    assert update.status_code == 200
    assert update.json()["is_active"] is False

    listing = client.get("/api/admin/coupons", headers=admin_headers)
    assert any(c["id"] == coupon_id for c in listing.json())

    delete = client.delete(f"/api/admin/coupons/{coupon_id}", headers=admin_headers)
    assert delete.status_code == 204
    listing_after = client.get("/api/admin/coupons", headers=admin_headers)
    assert not any(c["id"] == coupon_id for c in listing_after.json())


def test_non_admin_cannot_manage_coupons(client, auth_headers):
    headers, _ = auth_headers
    response = client.post(
        "/api/admin/coupons",
        headers=headers,
        json={"code": "NOPE", "discount_type": "percentage", "discount_value": 10},
    )
    assert response.status_code == 403


def test_admin_can_update_order_status(client, admin_headers, auth_headers, seed_catalog):
    headers, _ = auth_headers
    variant_id = str(seed_catalog["variant_in_stock"].id)
    client.post("/api/cart/items", headers=headers, json={"variant_id": variant_id, "quantity": 1})
    order_id = client.post(
        "/api/orders",
        headers=headers,
        json={
            "shipping_address": {
                "full_name": "Ava",
                "line1": "1 Main St",
                "city": "NYC",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "phone": "+15551234567",
            }
        },
    ).json()["id"]

    response = client.patch(
        f"/api/admin/orders/{order_id}/status", headers=admin_headers, json={"status": "shipped"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "shipped"

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
    assert len(response.json()) == 2  # active + inactive both visible to admin


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

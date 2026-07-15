def test_account_requires_authentication(client):
    response = client.get("/api/account/profile")
    assert response.status_code == 401


def test_get_and_update_profile(client, auth_headers):
    headers, user = auth_headers
    response = client.get("/api/account/profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == user["email"]

    response = client.patch(
        "/api/account/profile", headers=headers, json={"first_name": "Updated", "last_name": "Name"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Updated"
    assert body["full_name"] == "Updated Name"


def test_update_profile_duplicate_email_rejected(client, register_user, auth_headers):
    register_user(email="taken@example.com")
    headers, _ = auth_headers
    response = client.patch("/api/account/profile", headers=headers, json={"email": "taken@example.com"})
    assert response.status_code == 409


def test_change_password_success_and_relogin(client, register_user):
    data = register_user(email="pwchange@example.com", password="OldPass123!")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    response = client.post(
        "/api/account/password",
        headers=headers,
        json={
            "current_password": "OldPass123!",
            "new_password": "NewPass456!",
            "confirm_new_password": "NewPass456!",
        },
    )
    assert response.status_code == 204

    login = client.post("/api/auth/login", json={"email": "pwchange@example.com", "password": "NewPass456!"})
    assert login.status_code == 200


def test_change_password_wrong_current_rejected(client, auth_headers):
    headers, _ = auth_headers
    response = client.post(
        "/api/account/password",
        headers=headers,
        json={
            "current_password": "WrongPass123!",
            "new_password": "NewPass456!",
            "confirm_new_password": "NewPass456!",
        },
    )
    assert response.status_code == 401


def test_change_password_mismatched_confirmation_rejected(client, auth_headers):
    headers, _ = auth_headers
    response = client.post(
        "/api/account/password",
        headers=headers,
        json={
            "current_password": "TestPass123!",
            "new_password": "NewPass456!",
            "confirm_new_password": "Different789!",
        },
    )
    assert response.status_code == 422


def test_delete_account_requires_correct_password(client, register_user):
    data = register_user(email="deleteme@example.com", password="DeletePass123!")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    response = client.post(
        "/api/account/delete", headers=headers, json={"password": "WrongPass!", "confirm": True}
    )
    assert response.status_code == 401

    response = client.post(
        "/api/account/delete", headers=headers, json={"password": "DeletePass123!", "confirm": True}
    )
    assert response.status_code == 204

    login = client.post(
        "/api/auth/login", json={"email": "deleteme@example.com", "password": "DeletePass123!"}
    )
    assert login.status_code == 401


def _address_payload(**overrides):
    payload = {
        "full_name": "Jane Doe",
        "line1": "1 Market St",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94105",
        "country": "United States",
        "phone": "+14155550100",
    }
    payload.update(overrides)
    return payload


def test_address_crud_and_defaults(client, auth_headers):
    headers, _ = auth_headers

    response = client.post(
        "/api/account/addresses", headers=headers, json=_address_payload(is_default_shipping=True)
    )
    assert response.status_code == 201
    address_1 = response.json()
    assert address_1["is_default_shipping"] is True

    response = client.post(
        "/api/account/addresses",
        headers=headers,
        json=_address_payload(line1="2 Second St", is_default_shipping=True),
    )
    assert response.status_code == 201
    address_2 = response.json()
    assert address_2["is_default_shipping"] is True

    # setting a new default shipping address clears the previous one
    response = client.get("/api/account/addresses", headers=headers)
    addresses = response.json()
    first = next(a for a in addresses if a["id"] == address_1["id"])
    assert first["is_default_shipping"] is False

    response = client.patch(
        f"/api/account/addresses/{address_1['id']}", headers=headers, json={"city": "Oakland"}
    )
    assert response.status_code == 200
    assert response.json()["city"] == "Oakland"

    response = client.delete(f"/api/account/addresses/{address_2['id']}", headers=headers)
    assert response.status_code == 204

    response = client.get("/api/account/addresses", headers=headers)
    assert len(response.json()) == 1


def test_style_profile_get_default_and_update(client, auth_headers):
    headers, _ = auth_headers
    response = client.get("/api/account/style-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["preferred_colors"] == []

    response = client.put(
        "/api/account/style-profile",
        headers=headers,
        json={
            "gender_presentation": "women",
            "preferred_colors": ["black", "burgundy"],
            "disliked_colors": ["neon green"],
            "budget_min": 50,
            "budget_max": 300,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["preferred_colors"] == ["black", "burgundy"]
    assert body["budget_max"] == 300

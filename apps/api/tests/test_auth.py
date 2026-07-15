def test_register_creates_user_and_returns_token(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "newuser@example.com"
    assert body["user"]["role"] == "customer"
    assert body["user"]["full_name"] == "New User"
    assert "password" not in body["user"]
    assert "hashed_password" not in body["user"]


def test_register_normalizes_email_to_lowercase(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "Mixed.Case@Example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": "Case",
            "last_name": "Tester",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "mixed.case@example.com"


def test_register_duplicate_email_rejected(client, register_user):
    register_user(email="dupe@example.com")
    response = client.post(
        "/api/auth/register",
        json={
            "email": "dupe@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": "Dup",
            "last_name": "User",
        },
    )
    assert response.status_code == 409


def test_register_duplicate_email_case_insensitive_rejected(client, register_user):
    register_user(email="dupe2@example.com")
    response = client.post(
        "/api/auth/register",
        json={
            "email": "Dupe2@Example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": "Dup",
            "last_name": "Two",
        },
    )
    assert response.status_code == 409


def test_register_invalid_email_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": "Bad",
            "last_name": "Email",
        },
    )
    assert response.status_code == 422


def test_register_weak_password_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "weak@example.com",
            "password": "password",
            "confirm_password": "password",
            "first_name": "Weak",
            "last_name": "Pass",
        },
    )
    assert response.status_code == 422


def test_register_password_missing_special_char_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "nospecial@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
            "first_name": "No",
            "last_name": "Special",
        },
    )
    assert response.status_code == 422


def test_register_mismatched_confirmation_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "mismatch@example.com",
            "password": "SecurePass123!",
            "confirm_password": "DifferentPass123!",
            "first_name": "Mis",
            "last_name": "Match",
        },
    )
    assert response.status_code == 422


def test_login_success(client, register_user):
    register_user(email="login@example.com", password="MyPassword123!")
    response = client.post(
        "/api/auth/login", json={"email": "login@example.com", "password": "MyPassword123!"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_rejected(client, register_user):
    register_user(email="login2@example.com", password="MyPassword123!")
    response = client.post(
        "/api/auth/login", json={"email": "login2@example.com", "password": "WrongPassword!"}
    )
    assert response.status_code == 401


def test_login_unknown_email_rejected(client):
    response = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "WhoKnows123!"}
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers, user = auth_headers
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == user["email"]


def test_protected_route_rejects_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401

def test_register_creates_user_and_returns_token(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "SecurePass123!", "full_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "newuser@example.com"
    assert body["user"]["role"] == "customer"
    assert "password" not in body["user"]
    assert "hashed_password" not in body["user"]


def test_register_duplicate_email_rejected(client, register_user):
    register_user(email="dupe@example.com")
    response = client.post(
        "/api/auth/register",
        json={"email": "dupe@example.com", "password": "SecurePass123!", "full_name": "Dup"},
    )
    assert response.status_code == 409


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


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers, user = auth_headers
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == user["email"]

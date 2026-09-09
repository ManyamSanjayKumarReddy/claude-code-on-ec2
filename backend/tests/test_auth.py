import uuid


def unique_email():
    return f"user-{uuid.uuid4().hex}@example.com"


def register_payload(**overrides):
    payload = {
        "email": unique_email(),
        "password": "supersecret123",
        "full_name": "Test User",
    }
    payload.update(overrides)
    return payload


def test_register_creates_user(client):
    client.cookies.clear()
    response = client.post("/auth/register", json=register_payload(full_name="New User"))

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "New User"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_sets_auth_cookie(client):
    client.cookies.clear()
    response = client.post("/auth/register", json=register_payload())

    assert response.status_code == 201
    assert "access_token" in response.cookies


def test_register_rejects_duplicate_email(client):
    client.cookies.clear()
    payload = register_payload()
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409


def test_register_rejects_short_password(client):
    client.cookies.clear()
    response = client.post("/auth/register", json=register_payload(password="short"))

    assert response.status_code == 422


def test_register_rejects_invalid_email(client):
    client.cookies.clear()
    response = client.post("/auth/register", json=register_payload(email="not-an-email"))

    assert response.status_code == 422


def test_login_with_correct_credentials(client):
    client.cookies.clear()
    payload = register_payload()
    client.post("/auth/register", json=payload)
    client.cookies.clear()

    response = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})

    assert response.status_code == 200
    assert response.json()["email"] == payload["email"]
    assert "access_token" in response.cookies


def test_login_rejects_wrong_password(client):
    client.cookies.clear()
    payload = register_payload()
    client.post("/auth/register", json=payload)
    client.cookies.clear()

    response = client.post("/auth/login", json={"email": payload["email"], "password": "wrongpassword"})

    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    client.cookies.clear()
    response = client.post("/auth/login", json={"email": unique_email(), "password": "whatever123"})

    assert response.status_code == 401


def test_me_returns_current_user_when_authenticated(client):
    client.cookies.clear()
    payload = register_payload()
    client.post("/auth/register", json=payload)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == payload["email"]


def test_me_requires_authentication(client):
    client.cookies.clear()

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_logout_clears_session(client):
    client.cookies.clear()
    payload = register_payload()
    client.post("/auth/register", json=payload)

    logout_response = client.post("/auth/logout")
    me_response = client.get("/auth/me")

    assert logout_response.status_code == 204
    assert me_response.status_code == 401

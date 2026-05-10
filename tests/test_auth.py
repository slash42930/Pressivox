from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _register_payload(username: str) -> dict[str, str]:
    return {
        "username": username,
        "password": "test-pass-123",
    }


def test_register_and_login_flow() -> None:
    payload = _register_payload("auth-user")

    register = client.post("/api/v1/auth/register", json=payload)
    assert register.status_code in (201, 400)

    login = client.post("/api/v1/auth/login", json=payload)
    assert login.status_code == 200

    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["username"] == payload["username"]
    assert body["user"]["role"] in {"admin", "user"}


def test_refresh_returns_new_tokens() -> None:
    payload = _register_payload("auth-refresh-user")
    client.post("/api/v1/auth/register", json=payload)

    login = client.post("/api/v1/auth/login", json=payload)
    assert login.status_code == 200
    refresh_token = login.json()["refresh_token"]

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh.status_code == 200
    data = refresh.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_admin_check_requires_admin_role() -> None:
    # First created account in a DB is admin. Create a second account to validate non-admin access.
    client.post("/api/v1/auth/register", json=_register_payload("auth-admin-seed"))
    user_payload = _register_payload("auth-regular-user")
    client.post("/api/v1/auth/register", json=user_payload)
    user_login = client.post("/api/v1/auth/login", json=user_payload)
    assert user_login.status_code == 200
    user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    admin_check = client.get("/api/v1/auth/admin/check", headers=user_headers)
    assert admin_check.status_code == 403


def test_me_requires_authentication() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_login_accepts_case_insensitive_username() -> None:
    payload = _register_payload("MixedCaseUser")
    client.post("/api/v1/auth/register", json=payload)

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "MIXEDCASEUSER", "password": payload["password"]},
    )
    assert login.status_code == 200

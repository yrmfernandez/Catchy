"""Auth flow tests (register / login / me)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register(email: str, password: str = "password123"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def test_register_returns_token_and_user() -> None:
    resp = _register("alice@example.com")
    assert resp.status_code == 201
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "alice@example.com"


def test_duplicate_email_conflicts() -> None:
    _register("dup@example.com")
    assert _register("dup@example.com").status_code == 409


def test_login_and_me() -> None:
    _register("bob@example.com")
    login = client.post(
        "/api/v1/auth/login", json={"email": "bob@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "bob@example.com"


def test_login_wrong_password_rejected() -> None:
    _register("carol@example.com")
    resp = client.post(
        "/api/v1/auth/login", json={"email": "carol@example.com", "password": "wrongpass"}
    )
    assert resp.status_code == 401


def test_login_unknown_email_rejected() -> None:
    resp = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "password123"}
    )
    assert resp.status_code == 401


def test_me_requires_token() -> None:
    assert client.get("/api/v1/auth/me").status_code == 401


def test_short_password_rejected() -> None:
    resp = client.post(
        "/api/v1/auth/register", json={"email": "x@example.com", "password": "short"}
    )
    assert resp.status_code == 422

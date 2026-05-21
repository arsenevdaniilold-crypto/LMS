"""End-to-end auth flow through the ASGI app and the test database."""
import pytest

# Run every test in this module on the same session-scoped event loop as the
# session-scoped DB fixtures, so asyncpg connections never cross loops.
pytestmark = pytest.mark.asyncio(loop_scope="session")

REGISTER = "/api/auth/register"
LOGIN = "/api/auth/login"
LOGOUT = "/api/auth/logout"
ME = "/api/users/me"


async def _register(client, email="alice@example.com", password="password123", username="Alice"):
    return await client.post(
        REGISTER, json={"email": email, "password": password, "username": username}
    )


async def test_register_returns_user_and_sets_cookies(client):
    resp = await _register(client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["username"] == "Alice"
    assert body["is_admin"] is False
    assert "id" in body
    # auth cookies must be set
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


async def test_me_requires_authentication(client):
    resp = await client.get(ME)
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "NOT_AUTHENTICATED"


async def test_full_login_logout_cycle(client):
    # register (also logs in via cookies on the shared client jar)
    reg = await _register(client)
    assert reg.status_code == 201

    # /me works while authenticated
    me = await client.get(ME)
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"

    # logout clears the session
    out = await client.post(LOGOUT)
    assert out.status_code == 204

    # cookies are cleared -> /me now unauthorized
    client.cookies.clear()
    me_after = await client.get(ME)
    assert me_after.status_code == 401

    # login again with correct credentials
    login = await client.post(
        LOGIN, json={"email": "alice@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    assert "access_token" in login.cookies


async def test_login_wrong_password_is_401(client):
    await _register(client)
    client.cookies.clear()
    resp = await client.post(
        LOGIN, json={"email": "alice@example.com", "password": "WRONG-password"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "INVALID_CREDENTIALS"


async def test_duplicate_email_is_409(client):
    first = await _register(client)
    assert first.status_code == 201
    client.cookies.clear()
    dup = await _register(client, username="Alice2")
    assert dup.status_code == 409
    assert dup.json()["detail"]["code"] == "EMAIL_TAKEN"


async def test_register_validation_short_password(client):
    resp = await client.post(
        REGISTER, json={"email": "bob@example.com", "password": "short", "username": "Bob"}
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "VALIDATION_ERROR"

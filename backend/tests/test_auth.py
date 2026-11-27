"""Authentication, JWT security, and CORS tests."""

from datetime import timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.user import User


def test_healthcheck_and_cors_headers(client: TestClient) -> None:
    """Verify health endpoint and explicit CORS origin handling."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_register_normalizes_email_and_rejects_duplicates(client: TestClient) -> None:
    """Registering normalizes email case/whitespace and blocks duplicate registrations."""
    resp1 = client.post(
        "/api/v1/auth/register",
        json={"email": "  Alice@Example.COM ", "password": "StrongPassword123!"},
    )
    assert resp1.status_code == 201
    data = resp1.json()
    assert data["email"] == "alice@example.com"
    assert "password_hash" not in data

    resp2 = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "AnotherPassword123!"},
    )
    assert resp2.status_code == 409


def test_register_rejects_password_over_72_utf8_bytes(client: TestClient) -> None:
    """Passwords exceeding bcrypt's 72-byte limit are rejected cleanly with 422."""
    long_password = "a" * 73
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "longpass@example.com", "password": long_password},
    )
    assert response.status_code == 422


def test_login_anti_enumeration_returns_identical_401(client: TestClient) -> None:
    """Login returns identical 401 status and detail for unknown email and wrong password."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "ValidPassword123!"},
    )

    unknown_email_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "ValidPassword123!"},
    )
    wrong_password_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "WrongPassword123!"},
    )

    assert unknown_email_resp.status_code == 401
    assert wrong_password_resp.status_code == 401
    assert unknown_email_resp.json() == wrong_password_resp.json()


def test_login_and_me_success(client: TestClient) -> None:
    """Valid user can log in and retrieve their profile via /auth/me."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "password": "ValidPassword123!"},
    )

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "CAROL@example.com", "password": "ValidPassword123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "carol@example.com"


def test_rejects_expired_tampered_wrong_type_and_deleted_user_tokens(
    client: TestClient,
    db_session: Session,
) -> None:
    """get_current_user rejects expired, tampered, non-access, and deleted-user tokens."""
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "dave@example.com", "password": "ValidPassword123!"},
    )
    user_id = reg_resp.json()["id"]
    settings = get_settings()

    expired_token = create_access_token(user_id, expires_delta=timedelta(minutes=-5))
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        ).status_code
        == 401
    )

    tampered_token = jwt.encode(
        {"sub": str(user_id), "type": "access", "exp": 9999999999},
        "wrong-signing-secret-key-that-should-fail",
        algorithm=settings.JWT_ALGORITHM,
    )
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"},
        ).status_code
        == 401
    )

    wrong_type_token = jwt.encode(
        {"sub": str(user_id), "type": "refresh", "exp": 9999999999},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {wrong_type_token}"},
        ).status_code
        == 401
    )

    valid_token = create_access_token(user_id)
    user = db_session.get(User, user_id)
    assert user is not None
    db_session.delete(user)
    db_session.commit()

    assert (
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_token}"},
        ).status_code
        == 401
    )

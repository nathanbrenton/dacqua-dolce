from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.identity import User, UserSession
from app.services.sessions import hash_session_token

client = TestClient(app)


def csrf() -> str:
    response = client.get("/api/auth/csrf")

    assert response.status_code == 200

    return response.json()["csrf_token"]


def test_register_session_me_logout() -> None:
    email = f"auth-{uuid4()}@example.test"
    password = "correct-horse-battery-staple"

    csrf_token = csrf()

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
        },
        headers={
            "X-CSRF-Token": csrf_token,
        },
    )

    assert response.status_code == 201
    assert response.json()["authenticated"] is True
    assert response.json()["email"] == email
    assert response.json()["roles"] == ["customer"]

    session_token = client.cookies.get("dacqua_session")

    assert session_token is not None

    with SessionLocal() as db:
        session_record = db.scalar(
            select(UserSession).where(UserSession.token_hash == hash_session_token(session_token))
        )

        assert session_record is not None
        assert session_record.token_hash != session_token

    me_response = client.get("/api/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == email

    new_csrf = response.headers["X-CSRF-Token"]

    logout_response = client.post(
        "/api/auth/logout",
        headers={
            "X-CSRF-Token": new_csrf,
        },
    )

    assert logout_response.status_code == 204

    unauthorized = client.get("/api/auth/me")

    assert unauthorized.status_code == 401

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))

        if user is not None:
            db.delete(user)
            db.commit()


def test_registration_rejects_malformed_email() -> None:
    csrf_token = csrf()

    response = client.post(
        "/api/auth/register",
        json={
            "email": "malformed@example",
            "password": "correct-horse-battery-staple",
        },
        headers={
            "X-CSRF-Token": csrf_token,
        },
    )

    assert response.status_code == 422

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def settings_for(
    environment: str,
) -> Settings:
    return Settings(
        database_url=(
            "postgresql+psycopg://"
            "unused:unused@127.0.0.1/unused"
        ),
        environment=environment,
        session_cookie_secure=True,
        csrf_protection_enabled=True,
    )


def test_development_docs_remain_available() -> None:
    client = TestClient(
        create_app(
            settings_for("development")
        )
    )

    docs = client.get("/api/docs")
    schema = client.get("/openapi.json")

    assert docs.status_code == 200
    assert schema.status_code == 200


def test_production_docs_and_openapi_are_disabled() -> None:
    client = TestClient(
        create_app(
            settings_for("production")
        )
    )

    assert client.get(
        "/api/docs"
    ).status_code == 404

    assert client.get(
        "/openapi.json"
    ).status_code == 404


def test_production_security_headers() -> None:
    client = TestClient(
        create_app(
            settings_for("production")
        ),
        base_url="https://water.example",
    )

    response = client.get(
        "/api/auth/csrf"
    )

    assert response.status_code == 200

    assert (
        response.headers[
            "X-Content-Type-Options"
        ]
        == "nosniff"
    )
    assert (
        response.headers[
            "X-Frame-Options"
        ]
        == "DENY"
    )
    assert (
        response.headers[
            "Referrer-Policy"
        ]
        == "no-referrer"
    )

    permissions = response.headers[
        "Permissions-Policy"
    ]

    assert "camera=()" in permissions
    assert "microphone=()" in permissions
    assert "payment=()" in permissions

    csp = response.headers[
        "Content-Security-Policy"
    ]

    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp

    assert (
        response.headers[
            "Strict-Transport-Security"
        ]
        == "max-age=31536000"
    )

    assert (
        response.headers["Cache-Control"]
        == "no-store"
    )
    assert (
        response.headers["Pragma"]
        == "no-cache"
    )


def test_hsts_is_not_sent_over_plain_http() -> None:
    client = TestClient(
        create_app(
            settings_for("production")
        ),
        base_url="http://water.example",
    )

    response = client.get(
        "/api/auth/csrf"
    )

    assert (
        "Strict-Transport-Security"
        not in response.headers
    )


def test_development_does_not_receive_production_csp() -> None:
    client = TestClient(
        create_app(
            settings_for("development")
        )
    )

    response = client.get(
        "/api/auth/csrf"
    )

    assert (
        "Content-Security-Policy"
        not in response.headers
    )

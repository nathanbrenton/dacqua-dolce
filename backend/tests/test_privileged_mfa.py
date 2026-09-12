from datetime import UTC, datetime
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.identity import (
    RoleName,
    User,
    UserMfaRecoveryCode,
    UserRole,
)
from app.services.authentication import (
    attach_password,
)
from app.services.mfa import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    totp_code,
)
from app.services.passwords import (
    hash_password,
)


def csrf(
    client: TestClient,
) -> str:
    response = client.get(
        "/api/auth/csrf"
    )

    assert response.status_code == 200

    return response.json()[
        "csrf_token"
    ]


def test_totp_matches_rfc6238_sha1_vector() -> None:
    secret = (
        "GEZDGNBVGY3TQOJQ"
        "GEZDGNBVGY3TQOJQ"
    )

    assert (
        totp_code(
            secret,
            at_time=datetime.fromtimestamp(
                59,
                tz=UTC,
            ),
            period_seconds=30,
            digits=8,
        )
        == "94287082"
    )


def test_totp_secret_encryption_round_trip() -> None:
    key = Fernet.generate_key().decode(
        "ascii"
    )

    settings = Settings(
        database_url=(
            "postgresql+psycopg://"
            "unused:unused@localhost/unused"
        ),
        mfa_encryption_key=key,
    )

    secret = (
        "JBSWY3DPEHPK3PXP"
    )

    ciphertext = encrypt_totp_secret(
        secret,
        settings,
    )

    assert ciphertext != secret

    assert (
        decrypt_totp_secret(
            ciphertext,
            settings,
        )
        == secret
    )


def test_privileged_login_requires_mfa_enrollment() -> None:
    settings = get_settings()

    assert (
        settings.mfa_encryption_key
        is not None
    )

    email = (
        f"mfa-{uuid4()}@example.test"
    )
    password = (
        "correct-horse-battery-staple"
    )

    user_id = None

    with SessionLocal() as db:
        user = User(
            email=email,
        )

        attach_password(
            user,
            hash_password(password),
        )

        user.roles.append(
            UserRole(
                role=RoleName.manager,
            )
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

    client = TestClient(app)

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
        headers={
            "X-CSRF-Token": csrf(
                client
            ),
        },
    )

    assert login_response.status_code == 200

    login_payload = (
        login_response.json()
    )

    assert (
        login_payload["authenticated"]
        is False
    )
    assert (
        login_payload[
            "mfa_enrollment_required"
        ]
        is True
    )
    assert (
        login_payload["mfa_required"]
        is False
    )
    assert login_payload["roles"] == []

    denied = client.get(
        "/api/auth/sessions"
    )

    assert denied.status_code == 401
    assert (
        denied.json()["detail"]
        == "MFA verification required."
    )

    me_before = client.get(
        "/api/auth/me"
    )

    assert me_before.status_code == 200
    assert (
        me_before.json()[
            "mfa_enrollment_required"
        ]
        is True
    )

    enrollment = client.post(
        "/api/auth/mfa/enroll",
        headers={
            "X-CSRF-Token": csrf(
                client
            ),
        },
    )

    assert enrollment.status_code == 200

    enrollment_payload = (
        enrollment.json()
    )

    assert len(
        enrollment_payload[
            "recovery_codes"
        ]
    ) == settings.mfa_recovery_code_count

    secret = enrollment_payload[
        "secret"
    ]

    assert secret in (
        enrollment_payload[
            "provisioning_uri"
        ]
    )

    verification = client.post(
        "/api/auth/mfa/verify",
        json={
            "code": totp_code(
                secret,
                period_seconds=(
                    settings
                    .mfa_totp_period_seconds
                ),
                digits=(
                    settings
                    .mfa_totp_digits
                ),
            ),
        },
        headers={
            "X-CSRF-Token": csrf(
                client
            ),
        },
    )

    assert verification.status_code == 200

    payload = verification.json()

    assert payload["authenticated"] is True
    assert "manager" in payload["roles"]
    assert payload["mfa_required"] is False

    sessions = client.get(
        "/api/auth/sessions"
    )

    assert sessions.status_code == 200

    recovery_code = (
        enrollment_payload[
            "recovery_codes"
        ][0]
    )

    logout = client.post(
        "/api/auth/logout",
        headers={
            "X-CSRF-Token": csrf(
                client
            ),
        },
    )

    assert logout.status_code == 204

    second_login = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
        headers={
            "X-CSRF-Token": csrf(
                client
            ),
        },
    )

    assert second_login.status_code == 200
    assert (
        second_login.json()[
            "mfa_required"
        ]
        is True
    )

    recovery_verify = client.post(
        "/api/auth/mfa/verify",
        json={
            "code": recovery_code,
        },
        headers={
            "X-CSRF-Token": csrf(
                client
            ),
        },
    )

    assert recovery_verify.status_code == 200
    assert (
        recovery_verify.json()[
            "authenticated"
        ]
        is True
    )

    with SessionLocal() as db:
        used = db.scalar(
            select(
                UserMfaRecoveryCode
            ).where(
                UserMfaRecoveryCode.user_id
                == user_id,
                UserMfaRecoveryCode.used_at
                .is_not(None),
            )
        )

        assert used is not None

        user = db.get(
            User,
            user_id,
        )

        if user is not None:
            db.delete(user)
            db.commit()

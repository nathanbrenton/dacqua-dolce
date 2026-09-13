from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.email_config import (
    get_email_runtime_settings,
)
from app.db.session import SessionLocal
from app.main import app
from app.models.email import (
    EmailDelivery,
    EmailDeliveryStatus,
)
from app.models.email_verification import (
    EmailVerificationToken,
)
from app.models.identity import (
    RoleName,
    User,
    UserRole,
)
from app.services.email_verification import (
    complete_email_verification,
    generate_verification_token,
    hash_verification_token,
    issue_email_verification,
)

client = TestClient(app)


def csrf() -> str:
    response = client.get(
        "/api/auth/csrf"
    )

    assert response.status_code == 200

    return response.json()[
        "csrf_token"
    ]


def test_verification_token_is_random_and_hashed() -> None:
    first = generate_verification_token()
    second = generate_verification_token()

    assert first != second
    assert len(first) >= 32
    assert len(second) >= 32

    first_hash = (
        hash_verification_token(first)
    )

    assert first_hash != first
    assert len(first_hash) == 64
    assert first_hash == (
        hash_verification_token(first)
    )


def test_registration_marks_email_unverified_and_issues_email() -> None:
    email = (
        f"verify-{uuid4()}@example.test"
    )

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": (
                "correct-horse-battery-staple"
            ),
        },
        headers={
            "X-CSRF-Token": csrf(),
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["authenticated"] is True
    assert payload["email_verified"] is False

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.email == email
            )
        )

        assert user is not None
        assert user.email_verified_at is None

        token = db.scalar(
            select(
                EmailVerificationToken
            ).where(
                EmailVerificationToken.user_id
                == user.id
            )
        )

        assert token is not None
        assert len(token.token_hash) == 64

        delivery = db.scalar(
            select(
                EmailDelivery
            ).where(
                EmailDelivery.category
                == "email_verification",
                EmailDelivery
                .related_entity_id
                == str(user.id),
            )
            .order_by(
                EmailDelivery.created_at.desc()
            )
        )

        assert delivery is not None
        assert (
            delivery.status
            == EmailDeliveryStatus.suppressed
        )

        db.delete(user)
        db.commit()


def test_verification_is_single_use() -> None:
    email = (
        f"verify-service-{uuid4()}"
        "@example.test"
    )

    with SessionLocal() as db:
        user = User(
            email=email,
            email_verified_at=None,
        )

        user.roles.append(
            UserRole(
                role=RoleName.customer,
            )
        )

        db.add(user)
        db.flush()

        raw_token = issue_email_verification(
            db,
            user=user,
            settings=(
                get_email_runtime_settings()
            ),
            requested_ip_address=None,
            requested_user_agent=None,
        )

        assert raw_token is not None

        user_id = user.id

        db.commit()

    with SessionLocal() as db:
        assert complete_email_verification(
            db,
            raw_token=raw_token,
            request_ip_address=None,
            request_user_agent=None,
        )

        db.commit()

        user = db.get(
            User,
            user_id,
        )

        assert user is not None
        assert (
            user.email_verified_at
            is not None
        )

    with SessionLocal() as db:
        assert not complete_email_verification(
            db,
            raw_token=raw_token,
            request_ip_address=None,
            request_user_agent=None,
        )

        user = db.get(
            User,
            user_id,
        )

        if user is not None:
            db.delete(user)
            db.commit()


def test_resend_supersedes_previous_token() -> None:
    email = (
        f"verify-resend-{uuid4()}"
        "@example.test"
    )

    with SessionLocal() as db:
        user = User(
            email=email,
            email_verified_at=None,
        )

        user.roles.append(
            UserRole(
                role=RoleName.customer,
            )
        )

        db.add(user)
        db.flush()

        first = issue_email_verification(
            db,
            user=user,
            settings=(
                get_email_runtime_settings()
            ),
            requested_ip_address=None,
            requested_user_agent=None,
        )

        second = issue_email_verification(
            db,
            user=user,
            settings=(
                get_email_runtime_settings()
            ),
            requested_ip_address=None,
            requested_user_agent=None,
        )

        assert first is not None
        assert second is not None
        assert first != second

        first_record = db.scalar(
            select(
                EmailVerificationToken
            ).where(
                EmailVerificationToken.token_hash
                == hash_verification_token(
                    first
                )
            )
        )

        second_record = db.scalar(
            select(
                EmailVerificationToken
            ).where(
                EmailVerificationToken.token_hash
                == hash_verification_token(
                    second
                )
            )
        )

        assert first_record is not None
        assert second_record is not None

        assert (
            first_record.superseded_at
            is not None
        )
        assert (
            second_record.superseded_at
            is None
        )

        db.rollback()

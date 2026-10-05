import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.api import operations
from app.models.email import (
    EmailDeliveryStatus,
)
from app.models.identity import UserStatus


class ScalarResult:
    def __init__(
        self,
        values: list[object],
    ) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class CommunicationsDatabase:
    def __init__(
        self,
        deliveries: list[object],
    ) -> None:
        self.deliveries = deliveries
        self.queried = False

    def scalars(
        self,
        statement: object,
    ) -> ScalarResult:
        self.queried = True

        query = str(statement)

        assert "email_deliveries" in query

        return ScalarResult(
            self.deliveries,
        )


def test_communications_requires_operations_access(
    monkeypatch: Any,
) -> None:
    database = CommunicationsDatabase([])

    def deny(
        db: object,
        *,
        user: object,
    ) -> None:
        raise HTTPException(
            status_code=403,
            detail="Operations access required.",
        )

    monkeypatch.setattr(
        operations,
        "require_operations",
        deny,
    )

    with pytest.raises(
        HTTPException,
    ) as exc:
        operations.list_communications(
            database,  # type: ignore[arg-type]
            SimpleNamespace(
                id=uuid.uuid4(),
            ),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 403
    assert database.queried is False


def test_communications_response_is_bounded(
    monkeypatch: Any,
) -> None:
    created_at = datetime.now(UTC)
    sent_at = datetime.now(UTC)

    delivery = SimpleNamespace(
        id=uuid.uuid4(),
        category=(
            "quote_customer_receipt"
        ),
        related_entity_type=(
            "quote_request"
        ),
        related_entity_id=(
            str(uuid.uuid4())
        ),
        provider="postmark",
        sender=(
            "hello@example.test"
        ),
        recipient=(
            "customer@example.test"
        ),
        subject=(
            "We received your request"
        ),
        status=(
            EmailDeliveryStatus.sent
        ),
        provider_reference=(
            "provider-secret-reference"
        ),
        error_summary=(
            "internal provider detail"
        ),
        created_at=created_at,
        sent_at=sent_at,
    )

    database = CommunicationsDatabase(
        [delivery],
    )

    monkeypatch.setattr(
        operations,
        "require_operations",
        lambda db, user: None,
    )

    response = (
        operations.list_communications(
            database,  # type: ignore[arg-type]
            SimpleNamespace(
                id=uuid.uuid4(),
            ),  # type: ignore[arg-type]
        )
    )

    assert len(response) == 1

    payload = response[0].model_dump()

    assert payload == {
        "id": str(delivery.id),
        "category": (
            "quote_customer_receipt"
        ),
        "related_entity_type": (
            "quote_request"
        ),
        "related_entity_id": (
            delivery.related_entity_id
        ),
        "sender": (
            "hello@example.test"
        ),
        "recipient": (
            "customer@example.test"
        ),
        "subject": (
            "We received your request"
        ),
        "status": "sent",
        "requires_review": False,
        "created_at": (
            created_at.isoformat()
        ),
        "sent_at": (
            sent_at.isoformat()
        ),
    }

    assert (
        "provider_reference"
        not in payload
    )
    assert "provider" not in payload
    assert "error_summary" not in payload
    assert "body" not in payload
    assert "body_text" not in payload
    assert "body_html" not in payload

class DeliveryReviewDatabase:
    def __init__(self, user: object | None) -> None:
        self.user = user

    def get(
        self,
        model: object,
        entity_id: object,
    ) -> object | None:
        return self.user


def verification_failure(
    *,
    user_id: uuid.UUID,
) -> SimpleNamespace:
    return SimpleNamespace(
        category="email_verification",
        related_entity_type="user",
        related_entity_id=str(user_id),
        status=EmailDeliveryStatus.failed,
    )


def test_verified_user_email_failure_no_longer_requires_review() -> None:
    user_id = uuid.uuid4()
    database = DeliveryReviewDatabase(
        SimpleNamespace(
            status=UserStatus.active,
            email_verified_at=datetime.now(UTC),
        )
    )

    assert operations.email_delivery_requires_review(
        database,  # type: ignore[arg-type]
        delivery=verification_failure(user_id=user_id),
    ) is False


def test_disabled_user_email_failure_no_longer_requires_review() -> None:
    user_id = uuid.uuid4()
    database = DeliveryReviewDatabase(
        SimpleNamespace(
            status=UserStatus.disabled,
            email_verified_at=None,
        )
    )

    assert operations.email_delivery_requires_review(
        database,  # type: ignore[arg-type]
        delivery=verification_failure(user_id=user_id),
    ) is False


def test_unverified_active_user_email_failure_still_requires_review() -> None:
    user_id = uuid.uuid4()
    database = DeliveryReviewDatabase(
        SimpleNamespace(
            status=UserStatus.active,
            email_verified_at=None,
        )
    )

    assert operations.email_delivery_requires_review(
        database,  # type: ignore[arg-type]
        delivery=verification_failure(user_id=user_id),
    ) is True


def test_non_verification_failure_remains_reviewable() -> None:
    database = DeliveryReviewDatabase(None)
    delivery = SimpleNamespace(
        category="quote_customer_receipt",
        related_entity_type="quote_request",
        related_entity_id=str(uuid.uuid4()),
        status=EmailDeliveryStatus.failed,
    )

    assert operations.email_delivery_requires_review(
        database,  # type: ignore[arg-type]
        delivery=delivery,
    ) is True

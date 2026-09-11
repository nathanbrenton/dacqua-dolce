import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.api import operations
from app.models.quote import (
    QuoteRequestStatus,
)
from app.schemas.operations import (
    QuoteNotesUpdate,
)


class FakeDatabase:
    def __init__(
        self,
        quote: SimpleNamespace,
    ) -> None:
        self.quote = quote
        self.committed = False
        self.refreshed = False

    def get(
        self,
        model: object,
        identifier: uuid.UUID,
    ) -> SimpleNamespace:
        return self.quote

    def scalar(
        self,
        statement: object,
    ) -> None:
        return None

    def commit(self) -> None:
        self.committed = True

    def refresh(
        self,
        value: object,
    ) -> None:
        self.refreshed = True


def test_quote_notes_update_is_private_and_audited(
    monkeypatch: Any,
) -> None:
    quote_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    quote = SimpleNamespace(
        id=quote_id,
        product_id=None,
        name="Test Customer",
        email="customer@example.com",
        phone=None,
        message="Customer supplied message.",
        internal_notes=None,
        status=QuoteRequestStatus.new,
        created_at=datetime.now(UTC),
    )

    database = FakeDatabase(quote)

    audit: dict[str, object] = {}

    monkeypatch.setattr(
        operations,
        "require_operations",
        lambda db, user: None,
    )

    def capture_audit_event(
        db: object,
        **kwargs: object,
    ) -> None:
        audit.update(kwargs)

    monkeypatch.setattr(
        operations,
        "record_audit_event",
        capture_audit_event,
    )

    response = operations.update_quote_notes(
        quote_id,
        QuoteNotesUpdate(
            internal_notes=(
                "Called customer; awaiting reply."
            ),
        ),
        database,  # type: ignore[arg-type]
        SimpleNamespace(
            id=actor_id,
        ),  # type: ignore[arg-type]
    )

    assert database.committed is True
    assert database.refreshed is True
    assert quote.internal_notes == (
        "Called customer; awaiting reply."
    )
    assert response.internal_notes == (
        "Called customer; awaiting reply."
    )

    assert audit["action"] == (
        "quote.notes_updated"
    )

    metadata = audit["metadata"]

    assert metadata == {
        "had_notes": False,
        "has_notes": True,
    }

    assert (
        "Called customer"
        not in str(audit)
    )


def test_operations_quote_response_contains_notes() -> None:
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        product_id=None,
        name="Test Customer",
        email="customer@example.com",
        phone=None,
        message="Customer message.",
        internal_notes="Internal note.",
        status=QuoteRequestStatus.contacted,
        created_at=datetime.now(UTC),
    )

    database = FakeDatabase(quote)

    response = operations.operations_quote_read(
        database,  # type: ignore[arg-type]
        quote=quote,  # type: ignore[arg-type]
    )

    assert response.message == (
        "Customer message."
    )
    assert response.internal_notes == (
        "Internal note."
    )

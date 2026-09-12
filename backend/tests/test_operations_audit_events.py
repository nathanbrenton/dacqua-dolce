import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.api import operations


class ScalarResult:
    def __init__(
        self,
        values: list[object],
    ) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class AuditDatabase:
    def __init__(
        self,
        events: list[object],
    ) -> None:
        self.events = events
        self.queried = False

    def scalars(
        self,
        statement: object,
    ) -> ScalarResult:
        self.queried = True

        query = str(statement)
        assert "audit_events" in query

        return ScalarResult(self.events)


def test_audit_events_require_privileged_access(
    monkeypatch: Any,
) -> None:
    database = AuditDatabase([])

    def deny(
        db: object,
        *,
        user: object,
    ) -> None:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions.",
        )

    monkeypatch.setattr(
        operations,
        "require_privileged_operations",
        deny,
    )

    with pytest.raises(HTTPException) as exc:
        operations.list_audit_events(
            database,  # type: ignore[arg-type]
            SimpleNamespace(
                id=uuid.uuid4(),
            ),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 403
    assert database.queried is False


def test_audit_event_response_excludes_sensitive_context(
    monkeypatch: Any,
) -> None:
    event_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    created_at = datetime.now(UTC)

    event = SimpleNamespace(
        id=event_id,
        actor_user_id=actor_id,
        action="quote.notes_updated",
        entity_type="quote_request",
        entity_id=str(uuid.uuid4()),
        environment="development",
        metadata_json={
            "private": "do-not-expose",
        },
        ip_address="192.0.2.10",
        user_agent="Private user agent",
        created_at=created_at,
    )

    database = AuditDatabase([event])

    monkeypatch.setattr(
        operations,
        "require_privileged_operations",
        lambda db, user: None,
    )

    result = operations.list_audit_events(
        database,  # type: ignore[arg-type]
        SimpleNamespace(
            id=uuid.uuid4(),
        ),  # type: ignore[arg-type]
    )

    assert len(result) == 1

    payload = result[0].model_dump()

    assert payload == {
        "id": str(event_id),
        "actor_user_id": str(actor_id),
        "action": "quote.notes_updated",
        "entity_type": "quote_request",
        "entity_id": event.entity_id,
        "environment": "development",
        "created_at": created_at.isoformat(),
    }

    assert "metadata_json" not in payload
    assert "metadata" not in payload
    assert "ip_address" not in payload
    assert "user_agent" not in payload

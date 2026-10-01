import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.api import operations


class RowResult:
    def __init__(
        self,
        rows: list[tuple[object, str | None]],
    ) -> None:
        self.rows = rows

    def all(self) -> list[tuple[object, str | None]]:
        return self.rows


class AuditDatabase:
    def __init__(
        self,
        rows: list[tuple[object, str | None]],
    ) -> None:
        self.rows = rows
        self.queried = False

    def execute(
        self,
        statement: object,
    ) -> RowResult:
        self.queried = True

        query = str(statement)
        assert "audit_events" in query
        assert "users" in query

        return RowResult(self.rows)


def test_audit_events_require_developer_access(
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
        "require_audit_log_read",
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
            "request_id": "request-123",
            "outcome": "failed",
            "error_category": "runtime_error",
            "endpoint": "/api/example",
            "error_code": "safe_code",
        },
        ip_address="192.0.2.10",
        user_agent="Private user agent",
        created_at=created_at,
    )

    database = AuditDatabase([(event, "operator@example.com")])

    monkeypatch.setattr(
        operations,
        "require_audit_log_read",
        lambda db, user: None,
    )

    result = operations.list_audit_events(
        database,  # type: ignore[arg-type]
        SimpleNamespace(
            id=uuid.uuid4(),
        ),  # type: ignore[arg-type]
    )

    assert len(result.items) == 1
    assert result.page == 1
    assert result.page_size == 50
    assert result.has_more is False

    payload = result.items[0].model_dump()

    assert payload == {
        "id": str(event_id),
        "actor_user_id": str(actor_id),
        "actor_email": "operator@example.com",
        "action": "quote.notes_updated",
        "entity_type": "quote_request",
        "entity_id": event.entity_id,
        "environment": "development",
        "outcome": "failed",
        "request_id": "request-123",
        "error_category": "runtime_error",
        "endpoint": "/api/example",
        "error_code": "safe_code",
        "created_at": created_at.isoformat(),
    }

    assert "metadata_json" not in payload
    assert "metadata" not in payload
    assert "ip_address" not in payload
    assert "user_agent" not in payload


def test_audit_event_failed_action_defaults_to_failed_outcome() -> None:
    event = SimpleNamespace(
        id=uuid.uuid4(),
        actor_user_id=None,
        action="authentication.failed",
        entity_type="user",
        entity_id=None,
        environment="test",
        metadata_json={},
        ip_address=None,
        user_agent=None,
        created_at=datetime.now(UTC),
    )

    payload = operations.operations_audit_event_read(
        event=event,  # type: ignore[arg-type]
    )

    assert payload.outcome == "failed"
    assert payload.request_id is None


def test_audit_events_page_reports_more_rows(
    monkeypatch: Any,
) -> None:
    created_at = datetime.now(UTC)
    rows = []

    for index in range(11):
        rows.append(
            (
                SimpleNamespace(
                    id=uuid.uuid4(),
                    actor_user_id=None,
                    action=f"test.action_{index}",
                    entity_type="test_entity",
                    entity_id=str(index),
                    environment="test",
                    metadata_json={},
                    ip_address=None,
                    user_agent=None,
                    created_at=created_at,
                ),
                None,
            )
        )

    database = AuditDatabase(rows)
    monkeypatch.setattr(
        operations,
        "require_audit_log_read",
        lambda db, user: None,
    )

    result = operations.list_audit_events(
        database,  # type: ignore[arg-type]
        SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        page_size=10,
    )

    assert len(result.items) == 10
    assert result.has_more is True
    assert result.page_size == 10

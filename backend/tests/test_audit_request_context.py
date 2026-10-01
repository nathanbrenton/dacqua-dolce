from types import SimpleNamespace
from typing import Any

from app.core.request_context import reset_request_id, set_request_id
from app.services import audit


class AuditSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)


def test_record_audit_event_includes_request_id(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        audit,
        "get_settings",
        lambda: SimpleNamespace(environment="test"),
    )
    db = AuditSession()
    token = set_request_id("request-abc")

    try:
        event = audit.record_audit_event(
            db,  # type: ignore[arg-type]
            action="test.action",
            entity_type="test_entity",
            metadata={"safe": "value"},
        )
    finally:
        reset_request_id(token)

    assert event.metadata_json == {
        "safe": "value",
        "request_id": "request-abc",
    }
    assert db.added == [event]

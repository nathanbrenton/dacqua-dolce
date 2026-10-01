from types import SimpleNamespace
from typing import Any

import pytest
from starlette.requests import Request

from app.api import authentication
from app.core.request_context import reset_request_id, set_request_id


class FailureAuditDatabase:
    def __init__(self) -> None:
        self.rollback_calls = 0
        self.commit_calls = 0

    def rollback(self) -> None:
        self.rollback_calls += 1

    def commit(self) -> None:
        self.commit_calls += 1


def build_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "https",
            "path": "/api/auth/email-verification/complete",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 443),
        }
    )


def test_email_verification_runtime_error_is_safely_audited(
    monkeypatch: Any,
) -> None:
    database = FailureAuditDatabase()
    recorded: list[dict[str, object]] = []

    monkeypatch.setattr(
        authentication,
        "rate_limit_or_reject",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        authentication,
        "get_email_runtime_settings",
        lambda: object(),
    )

    def fail_completion(*args: object, **kwargs: object) -> bool:
        raise RuntimeError("simulated secret-bearing internal failure")

    monkeypatch.setattr(
        authentication,
        "complete_email_verification",
        fail_completion,
    )

    def capture_audit(*args: object, **kwargs: object) -> object:
        recorded.append(dict(kwargs))
        return object()

    monkeypatch.setattr(
        authentication,
        "record_audit_event",
        capture_audit,
    )

    token = set_request_id("request-failure-test")

    try:
        with pytest.raises(RuntimeError):
            authentication.verify_email_address(
                SimpleNamespace(token="raw-verification-secret"),  # type: ignore[arg-type]
                build_request(),
                database,  # type: ignore[arg-type]
                SimpleNamespace(
                    request_user_agent_max_length=512,
                ),  # type: ignore[arg-type]
            )
    finally:
        reset_request_id(token)

    assert database.rollback_calls == 1
    assert database.commit_calls == 1
    assert len(recorded) == 1

    event = recorded[0]
    assert event["action"] == (
        "authentication.email_verification.failed"
    )
    assert event["entity_type"] == "email_verification"
    assert event["metadata"] == {
        "outcome": "failed",
        "error_category": "runtime_error",
        "endpoint": "/api/auth/email-verification/complete",
        "error_code": "verification_completion_exception",
    }
    assert "raw-verification-secret" not in str(event)
    assert "secret-bearing" not in str(event)

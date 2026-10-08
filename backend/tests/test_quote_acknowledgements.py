from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.email_config import EmailRuntimeSettings
from app.services import quote_acknowledgements as ack


class FakeSession:
    def __init__(self, counts=()):
        self.counts = iter(counts)
        self.locks = 0

    def execute(self, statement, values):
        assert "pg_advisory_xact_lock" in str(statement)
        assert values["key"] == ack.LOCK_KEY
        self.locks += 1

    def scalar(self, statement):
        return next(self.counts)

    def flush(self):
        pass


def test_default_quote_acks_disabled_and_audited(monkeypatch):
    calls = []

    def fake_deliver(db, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(error_summary=None)

    monkeypatch.setattr(ack, "deliver_email", fake_deliver)
    settings = EmailRuntimeSettings(_env_file=None)
    assert settings.quote_ack_enabled is False
    db = FakeSession()
    result = ack.deliver_quote_acknowledgement(
        db, settings=settings, quote_id="uuid-generated-by-server",
        recipient=" PERSON@EXAMPLE.TEST ",
    )
    assert db.locks == 1
    assert result.error_summary == "acknowledgements_disabled"
    assert calls[0]["message"].recipient == "person@example.test"
    assert calls[0]["settings"].email_provider == "disabled"
    assert "uuid-generated-by-server" in calls[0]["message"].body_text


@pytest.mark.parametrize(
    ("counts", "expected"),
    [((1, 0), "recipient_cooldown"), ((0, 20), "global_acknowledgement_limit")],
)
def test_limits_suppress_without_sending(monkeypatch, counts, expected):
    calls = []

    def fake_deliver(db, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(error_summary=None)

    monkeypatch.setattr(ack, "deliver_email", fake_deliver)
    db = FakeSession(counts)
    settings = EmailRuntimeSettings(
        _env_file=None, quote_ack_enabled=True,
        quote_ack_message_stream="website-acknowledgements",
    )
    result = ack.deliver_quote_acknowledgement(
        db, settings=settings, quote_id="reference", recipient="person@example.test",
    )
    assert result.error_summary == expected
    assert calls[0]["settings"].email_provider == "disabled"


def test_allowed_uses_dedicated_stream(monkeypatch):
    calls = []

    def fake_deliver(db, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(error_summary=None)

    monkeypatch.setattr(ack, "deliver_email", fake_deliver)
    settings = EmailRuntimeSettings(
        _env_file=None, quote_ack_enabled=True,
        quote_ack_message_stream="website-acknowledgements",
    )
    ack.deliver_quote_acknowledgement(
        FakeSession((0, 0)), settings=settings,
        quote_id="reference", recipient="person@example.test",
    )
    assert calls[0]["message_stream"] == "website-acknowledgements"
    assert calls[0]["settings"].email_provider == settings.email_provider


def test_refuses_shared_outbound_stream():
    with pytest.raises(ValidationError):
        EmailRuntimeSettings(_env_file=None, quote_ack_message_stream="outbound")

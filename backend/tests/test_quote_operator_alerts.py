import uuid
from types import SimpleNamespace
from typing import Any

from app.api import quotes
from app.core.email_config import EmailRuntimeSettings


def _quote() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        inquiry_context="expert_inquiry",
        email="customer@example.test",
        user_id=None,
        name="Example Customer",
        phone=None,
        recommendation_decision=None,
        recommendation_policy_version=None,
        recommendation_context=None,
        message="Hard water spots.",
    )


def _capture_operator_alerts(
    monkeypatch: Any,
    settings: EmailRuntimeSettings,
) -> list[dict[str, Any]]:
    sent: list[dict[str, Any]] = []

    def fake_deliver(db: object, **kwargs: Any) -> None:
        sent.append(kwargs)

    monkeypatch.setattr(quotes, "get_email_runtime_settings", lambda: settings)
    monkeypatch.setattr(
        quotes,
        "deliver_quote_acknowledgement",
        lambda db, **kwargs: None,
    )
    monkeypatch.setattr(quotes, "deliver_email", fake_deliver)
    return sent


def test_operator_alert_goes_to_each_configured_inbox(monkeypatch: Any) -> None:
    sent = _capture_operator_alerts(
        monkeypatch,
        EmailRuntimeSettings(
            email_operator_to="owner@example.test, staff@example.test",
        ),
    )
    quote = _quote()

    quotes.send_quote_emails(db=object(), quote=quote, product=None)

    assert [alert["message"].recipient for alert in sent] == [
        "owner@example.test",
        "staff@example.test",
    ]
    assert {alert["category"] for alert in sent} == {
        "quote_operator_notification",
    }
    assert {alert["related_entity_id"] for alert in sent} == {str(quote.id)}


def test_blank_operator_setting_sends_no_alert(monkeypatch: Any) -> None:
    sent = _capture_operator_alerts(
        monkeypatch,
        EmailRuntimeSettings(email_operator_to=""),
    )

    quotes.send_quote_emails(db=object(), quote=_quote(), product=None)

    assert sent == []

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
        preferred_contact_method=None,
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


def test_operator_alert_is_brief(monkeypatch: Any) -> None:
    sent = _capture_operator_alerts(
        monkeypatch,
        EmailRuntimeSettings(email_operator_to="owner@example.test"),
    )
    quote = _quote()
    quote.inquiry_context = "product_inquiry"
    quote.phone = "+1 555 010 0100"
    quote.preferred_contact_method = "text"
    quote.recommendation_context = {"source_water": "municipal", "bathrooms": "2"}
    quote.recommendation_decision = {"title": "Softened water", "code": "salt_free"}
    product = SimpleNamespace(name="Harmony - Pureline Duo", product_family="Harmony")

    quotes.send_quote_emails(db=object(), quote=quote, product=product)

    message = sent[0]["message"]
    assert message.subject == "New product inquiry — Example Customer"
    assert message.body_text.splitlines() == [
        "Name: Example Customer",
        "Email: customer@example.test",
        "Phone: +1 555 010 0100",
        "Prefers: Text message",
        "Product family: Harmony",
        "",
        "Message:",
        "Hard water spots.",
    ]


def test_operator_alert_leaves_out_the_configuration_summary(
    monkeypatch: Any,
) -> None:
    sent = _capture_operator_alerts(
        monkeypatch,
        EmailRuntimeSettings(email_operator_to="owner@example.test"),
    )
    quote = _quote()
    quote.message = "\n".join([
        "Customer-requested configuration (NOT a priced or approved order):",
        "Catalog reference SKU: DD15CATRV (Essence)",
        "Requested valve: clack",
        "Confirm availability, compatibility, commercial terms, and pricing before ordering.",
    ]) + "\n\nI need the cleanest water for coffee."

    quotes.send_quote_emails(db=object(), quote=quote, product=None)

    lines = sent[0]["message"].body_text.splitlines()
    assert lines[-2:] == ["Message:", "I need the cleanest water for coffee."]
    assert "SKU" not in sent[0]["message"].body_text
    assert "Full details" not in sent[0]["message"].body_text


def test_operator_alert_configuration_without_customer_text(
    monkeypatch: Any,
) -> None:
    sent = _capture_operator_alerts(
        monkeypatch,
        EmailRuntimeSettings(email_operator_to="owner@example.test"),
    )
    quote = _quote()
    quote.message = (
        "Customer-requested configuration (NOT a priced or approved order):\n"
        "Catalog reference SKU: DD15CATRV (Essence)"
    )

    quotes.send_quote_emails(db=object(), quote=quote, product=None)

    assert sent[0]["message"].body_text.splitlines()[-2:] == [
        "Message:",
        "(No message)",
    ]


def test_operator_alert_without_product_or_phone(monkeypatch: Any) -> None:
    sent = _capture_operator_alerts(
        monkeypatch,
        EmailRuntimeSettings(email_operator_to="owner@example.test"),
    )

    quotes.send_quote_emails(db=object(), quote=_quote(), product=None)

    message = sent[0]["message"]
    assert message.subject == "New expert inquiry — Example Customer"
    assert "D'Acqua Dolce" not in message.subject
    assert "Phone: Not given" in message.body_text
    assert "Prefers: Not given" in message.body_text
    assert "Product family: None chosen" in message.body_text


def test_operator_alert_subject_flattens_the_name(monkeypatch: Any) -> None:
    sent = _capture_operator_alerts(
        monkeypatch,
        EmailRuntimeSettings(email_operator_to="owner@example.test"),
    )
    quote = _quote()
    quote.name = "  Jamie \n  Smith "

    quotes.send_quote_emails(db=object(), quote=quote, product=None)

    assert sent[0]["message"].subject == "New expert inquiry — Jamie Smith"

import pytest
from fastapi import Request
from pydantic import ValidationError

from app.api import support
from app.api.support import support_request_is_trapped, support_subject
from app.schemas.support import SupportRequestCreate


def test_support_request_normalizes_contact_fields() -> None:
    payload = SupportRequestCreate(
        kind="warranty",
        name="  Jamie Example  ",
        email="  JAMIE@EXAMPLE.COM ",
        phone="9495551234",
        product_id=None,
        message="  Please help with the warranty document.  ",
        website="   ",
    )

    assert payload.name == "Jamie Example"
    assert payload.email == "jamie@example.com"
    assert payload.phone == "+19495551234"
    assert payload.message == "Please help with the warranty document."
    assert payload.website is None
    assert support_request_is_trapped(payload) is False


def test_support_request_honeypot_flags_nonblank_website() -> None:
    payload = SupportRequestCreate(
        kind="general_support",
        name="Automated Visitor",
        email="visitor@example.com",
        message="Hello",
        website="https://example.invalid",
    )

    assert support_request_is_trapped(payload) is True


def test_trapped_support_request_returns_success_without_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = SupportRequestCreate(
        kind="general_support",
        name="Automated Visitor",
        email="visitor@example.com",
        message="Hello",
        website="filled-by-bot.example",
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/support",
            "headers": [],
            "client": ("192.0.2.55", 12345),
        }
    )

    def unexpected_optional_user(_request: Request) -> None:
        raise AssertionError("trapped submission must stop before account/database work")

    monkeypatch.setattr(support, "optional_user", unexpected_optional_user)

    result = support.create_support_request(payload, request)

    assert result.status == "received"
    assert "support request was received" in result.message.lower()


def test_support_request_rejects_blank_message() -> None:
    with pytest.raises(ValidationError):
        SupportRequestCreate(
            kind="general_support",
            name="Jamie Example",
            email="jamie@example.com",
            message="   ",
        )


def test_support_subject_keeps_product_context() -> None:
    assert support_subject("warranty", product_name="Origin RO") == (
        "Warranty support — Origin RO"
    )
    assert support_subject("general_support", product_name=None) == "General support"

"""Preferred contact method: email, call or text; calls and texts need a phone."""
import pytest
from pydantic import ValidationError

from app.core.contact_method import PHONE_REQUIRED_MESSAGE, contact_method_label
from app.schemas.account import CustomerProfileUpdate
from app.schemas.quote import QuoteRequestCreate
from app.schemas.support import SupportRequestCreate


def quote(**overrides: object) -> QuoteRequestCreate:
    values: dict[str, object] = {"name": "Jamie", "email": "jamie@example.test"}
    values.update(overrides)
    return QuoteRequestCreate.model_validate(values)


def support(**overrides: object) -> SupportRequestCreate:
    values: dict[str, object] = {
        "kind": "general_support",
        "name": "Jamie",
        "email": "jamie@example.test",
        "message": "Help, please.",
    }
    values.update(overrides)
    return SupportRequestCreate.model_validate(values)


def profile(**overrides: object) -> CustomerProfileUpdate:
    return CustomerProfileUpdate.model_validate(overrides)


BUILDERS = [quote, support, profile]


@pytest.mark.parametrize("build", BUILDERS)
def test_preference_is_optional_and_email_needs_no_phone(build) -> None:
    assert build().preferred_contact_method is None
    assert build(preferred_contact_method="email").preferred_contact_method == "email"


@pytest.mark.parametrize("build", BUILDERS)
@pytest.mark.parametrize("method", ["call", "text"])
def test_call_or_text_needs_a_phone(build, method: str) -> None:
    with pytest.raises(ValidationError, match=PHONE_REQUIRED_MESSAGE):
        build(preferred_contact_method=method)
    with pytest.raises(ValidationError, match=PHONE_REQUIRED_MESSAGE):
        build(preferred_contact_method=method, phone="   ")

    accepted = build(preferred_contact_method=method, phone="(951) 555-0142")
    assert accepted.preferred_contact_method == method
    assert accepted.phone == "+19515550142"


@pytest.mark.parametrize("build", BUILDERS)
def test_unknown_method_is_rejected(build) -> None:
    with pytest.raises(ValidationError):
        build(preferred_contact_method="fax", phone="(951) 555-0142")


def test_labels() -> None:
    assert contact_method_label("email") == "Email"
    assert contact_method_label("call") == "Phone call"
    assert contact_method_label("text") == "Text message"
    assert contact_method_label(None) is None
    assert contact_method_label("fax") is None

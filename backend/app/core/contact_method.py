"""How a customer prefers to be contacted: email, a phone call, or a text."""

from typing import Literal

ContactMethod = Literal["email", "call", "text"]

CONTACT_METHOD_VALUES: tuple[str, ...] = ("email", "call", "text")

CONTACT_METHOD_LABELS: dict[str, str] = {
    "email": "Email",
    "call": "Phone call",
    "text": "Text message",
}

PHONE_REQUIRED_MESSAGE = "Add a phone number so we can call or text you."


def require_phone_for_contact_method(
    method: str | None,
    phone: str | None,
) -> None:
    """Calls and texts need a phone number; email never does."""
    if method in {"call", "text"} and not phone:
        raise ValueError(PHONE_REQUIRED_MESSAGE)


def contact_method_label(method: object) -> str | None:
    return CONTACT_METHOD_LABELS.get(method) if isinstance(method, str) else None

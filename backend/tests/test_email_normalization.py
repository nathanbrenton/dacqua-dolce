import pytest
from pydantic import ValidationError

from app.core.email import (
    normalize_email_address,
)
from app.schemas.authentication import (
    AccountRegistrationRequest,
)
from app.schemas.quote import (
    QuoteRequestCreate,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "Customer@Example.COM",
            "customer@example.com",
        ),
        (
            "  customer@example.com  ",
            "customer@example.com",
        ),
    ],
)
def test_normalize_email_address(
    raw: str,
    expected: str,
) -> None:
    assert normalize_email_address(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "customer",
        "customer@example",
        "@example.com",
        "customer@",
        "customer @example.com",
    ],
)
def test_invalid_email_rejected(
    raw: str,
) -> None:
    with pytest.raises(ValueError):
        normalize_email_address(raw)


def test_registration_uses_shared_email_validation() -> None:
    with pytest.raises(ValidationError):
        AccountRegistrationRequest(
            email="customer@example",
            password="correct-horse-battery-staple",
        )


def test_quote_uses_shared_email_validation() -> None:
    with pytest.raises(ValidationError):
        QuoteRequestCreate(
            name="Test Customer",
            email="customer@example",
        )

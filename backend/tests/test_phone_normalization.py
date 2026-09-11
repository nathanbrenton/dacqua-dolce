import pytest

from app.core.phone import (
    normalize_us_phone,
)
from app.schemas.account import (
    CustomerProfileUpdate,
)
from app.schemas.quote import (
    QuoteRequestCreate,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "9495551234",
            "+19495551234",
        ),
        (
            "(949) 555-1234",
            "+19495551234",
        ),
        (
            "+1 (949) 555-1234",
            "+19495551234",
        ),
        (
            "949.555.1234",
            "+19495551234",
        ),
        ("   ", None),
        (None, None),
    ],
)
def test_normalize_us_phone(
    raw: str | None,
    expected: str | None,
) -> None:
    assert normalize_us_phone(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "949555123",
        "94955512345",
        "abc9495551234",
        "9495551234 ext 2",
        "1495551234",
        "9491551234",
    ],
)
def test_invalid_phone_rejected(
    raw: str,
) -> None:
    with pytest.raises(ValueError):
        normalize_us_phone(raw)


def test_quote_schema_normalizes_phone() -> None:
    payload = QuoteRequestCreate(
        name="Test Customer",
        email="test@example.com",
        phone="9495551234",
    )

    assert payload.phone == "+19495551234"


def test_profile_schema_normalizes_phone() -> None:
    payload = CustomerProfileUpdate(
        phone="(949) 555-1234"
    )

    assert payload.phone == "+19495551234"

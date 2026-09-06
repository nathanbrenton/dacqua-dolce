import pytest
from pydantic import ValidationError

from app.schemas.quote import (
    QuoteRequestCreate,
)


def test_quote_email_is_normalized() -> None:
    payload = QuoteRequestCreate(
        name=" Test Customer ",
        email=" PERSON@EXAMPLE.TEST ",
        message=" Interested in this system. ",
    )

    assert payload.name == "Test Customer"
    assert payload.email == "person@example.test"
    assert payload.message == "Interested in this system."


def test_quote_requires_email_shape() -> None:
    with pytest.raises(ValidationError):
        QuoteRequestCreate(
            name="Test Customer",
            email="not-an-email",
        )

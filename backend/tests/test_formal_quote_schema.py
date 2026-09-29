import uuid

import pytest
from pydantic import ValidationError

from app.schemas.operations import FormalQuoteCreate


def test_formal_quote_requires_at_least_one_line() -> None:
    with pytest.raises(ValidationError):
        FormalQuoteCreate(items=[])


def test_formal_quote_cleans_customer_note() -> None:
    payload = FormalQuoteCreate(
        items=[
            {
                "product_id": uuid.uuid4(),
                "quantity": 2,
            }
        ],
        customer_note="  Confirmed during assisted review.  ",
    )

    assert payload.customer_note == "Confirmed during assisted review."
    assert payload.items[0].quantity == 2
    assert payload.items[0].unit_amount_minor is None

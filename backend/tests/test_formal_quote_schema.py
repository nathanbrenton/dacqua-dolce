import uuid

import pytest
from pydantic import ValidationError

from app.schemas.operations import FormalQuoteCreate


def address() -> dict[str, object]:
    return {
        "recipient_name": "Dory Tang",
        "line1": "123 Ocean Ave",
        "line2": None,
        "city": "Irvine",
        "region_code": "CA",
        "postal_code": "92618",
        "country_code": "US",
        "phone": "+19495551234",
    }


def test_formal_quote_requires_at_least_one_line() -> None:
    with pytest.raises(ValidationError):
        FormalQuoteCreate(
            items=[],
            delivery_address=address(),
            billing_address=address(),
        )


def test_formal_quote_cleans_customer_note_and_keeps_addresses() -> None:
    payload = FormalQuoteCreate(
        items=[
            {
                "product_id": uuid.uuid4(),
                "quantity": 2,
            }
        ],
        delivery_address=address(),
        billing_address=address(),
        customer_note="  Confirmed during assisted review.  ",
    )

    assert payload.customer_note == "Confirmed during assisted review."
    assert payload.items[0].quantity == 2
    assert payload.items[0].unit_amount_minor is None
    assert payload.delivery_address.country_code == "US"


def test_commercial_adjustments_enforce_charge_and_credit_signs() -> None:
    common = {
        "items": [
            {
                "product_id": uuid.uuid4(),
                "quantity": 1,
            }
        ],
        "delivery_address": address(),
        "billing_address": address(),
    }

    payload = FormalQuoteCreate(
        **common,
        charges=[
            {
                "kind": "shipping",
                "label": "Freight",
                "amount_minor": 25000,
            },
            {
                "kind": "discount",
                "label": "Referral discount",
                "amount_minor": -10000,
            },
        ],
    )
    assert [charge.amount_minor for charge in payload.charges] == [25000, -10000]

    with pytest.raises(ValidationError):
        FormalQuoteCreate(
            **common,
            charges=[
                {
                    "kind": "discount",
                    "label": "Bad sign",
                    "amount_minor": 10000,
                }
            ],
        )

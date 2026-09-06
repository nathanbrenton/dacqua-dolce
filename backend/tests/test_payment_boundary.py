from dataclasses import fields

from app.models.commerce import (
    PaymentProviderReference,
)
from app.services.payment_provider import (
    CheckoutSessionRequest,
    PaymentMethodDisplay,
)

FORBIDDEN_PAYMENT_FIELDS = {
    "pan",
    "full_pan",
    "card_number",
    "cvv",
    "cvc",
    "security_code",
    "expiration",
    "expiration_date",
    "expiry",
    "track_data",
    "track1",
    "track2",
    "pin",
    "pin_block",
    "raw_payload",
    "provider_raw_payload",
}


def test_checkout_request_has_no_card_data_fields() -> None:
    request_fields = {field.name for field in fields(CheckoutSessionRequest)}

    assert request_fields.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)


def test_payment_display_metadata_is_minimal() -> None:
    display_fields = {field.name for field in fields(PaymentMethodDisplay)}

    assert display_fields == {
        "method_type",
        "brand",
        "last4",
    }


def test_payment_table_has_no_forbidden_fields() -> None:
    column_names = {column.name for column in PaymentProviderReference.__table__.columns}

    assert column_names.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)

from dataclasses import fields

from app.models.commerce import (
    PaymentProviderEvent,
    PaymentProviderReference,
)
from app.services.payment_events import VerifiedPaymentEvent
from app.services.payment_provider import (
    CheckoutSessionRequest,
    PaymentMethodDisplay,
    PaymentOperationResult,
    PaymentProviderCapabilities,
    PaymentProviderDescriptor,
    PaymentRefundRequest,
    PaymentVoidRequest,
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


def test_verified_event_contract_has_no_card_data_fields() -> None:
    event_fields = {field.name for field in fields(VerifiedPaymentEvent)}

    assert event_fields.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)


def test_payment_event_table_has_no_forbidden_fields() -> None:
    column_names = {column.name for column in PaymentProviderEvent.__table__.columns}

    assert column_names.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)


def test_payment_provider_descriptor_has_no_card_data_fields() -> None:
    descriptor_fields = {field.name for field in fields(PaymentProviderDescriptor)}
    capability_fields = {field.name for field in fields(PaymentProviderCapabilities)}

    assert descriptor_fields.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)
    assert capability_fields.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)


def test_refund_void_command_contracts_have_no_card_data_fields() -> None:
    refund_fields = {field.name for field in fields(PaymentRefundRequest)}
    void_fields = {field.name for field in fields(PaymentVoidRequest)}
    result_fields = {field.name for field in fields(PaymentOperationResult)}

    assert refund_fields.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)
    assert void_fields.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)
    assert result_fields.isdisjoint(FORBIDDEN_PAYMENT_FIELDS)

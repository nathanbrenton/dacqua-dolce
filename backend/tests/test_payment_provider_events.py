import uuid

import pytest

from app.models.audit import AuditEvent
from app.models.commerce import (
    Order,
    OrderStatus,
    PaymentProviderEvent,
    PaymentProviderReference,
    PaymentReferenceStatus,
)
from app.services.payment_events import (
    PaymentEventError,
    VerifiedPaymentEvent,
    apply_verified_payment_event,
)
from app.services.payment_provider import PaymentMethodDisplay


class EventDatabase:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.existing_event: PaymentProviderEvent | None = None

    def scalar(self, statement: object):
        query = str(statement)
        if "FROM payment_provider_events" in query:
            return self.existing_event
        raise AssertionError(query)

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        for value in self.added:
            if getattr(value, "id", None) is None and hasattr(value, "id"):
                value.id = uuid.uuid4()


def make_order_and_reference():
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=240000,
        charges_amount_minor=10000,
        total_amount_minor=250000,
        currency="USD",
    )
    reference = PaymentProviderReference(
        id=uuid.uuid4(),
        order_id=order.id,
        provider="sandbox-gateway",
        provider_checkout_id="checkout_123",
        status=PaymentReferenceStatus.pending,
    )
    return order, reference


def successful_event(**overrides):
    values = {
        "provider": "sandbox-gateway",
        "provider_event_id": "event_123",
        "status": PaymentReferenceStatus.succeeded,
        "amount_minor": 250000,
        "currency": "USD",
        "provider_payment_id": "payment_123",
        "provider_customer_id": "customer_123",
        "payment_method": PaymentMethodDisplay(
            method_type="card",
            brand="visa",
            last4="4242",
        ),
    }
    values.update(overrides)
    return VerifiedPaymentEvent(**values)


def test_successful_verified_event_marks_order_paid() -> None:
    db = EventDatabase()
    order, reference = make_order_and_reference()

    result = apply_verified_payment_event(
        db,  # type: ignore[arg-type]
        payment_reference=reference,
        order=order,
        verified_event=successful_event(),
    )

    assert result.duplicate is False
    assert result.order_became_paid is True
    assert order.status == OrderStatus.paid
    assert reference.status == PaymentReferenceStatus.succeeded
    assert reference.provider_payment_id == "payment_123"
    assert reference.payment_method_last4 == "4242"
    assert any(isinstance(value, PaymentProviderEvent) for value in db.added)
    assert any(isinstance(value, AuditEvent) for value in db.added)


def test_duplicate_provider_event_is_idempotent() -> None:
    db = EventDatabase()
    order, reference = make_order_and_reference()
    existing = PaymentProviderEvent(
        id=uuid.uuid4(),
        payment_reference_id=reference.id,
        provider=reference.provider,
        provider_event_id="event_123",
        status=PaymentReferenceStatus.succeeded,
        amount_minor=250000,
        currency="USD",
    )
    db.existing_event = existing

    result = apply_verified_payment_event(
        db,  # type: ignore[arg-type]
        payment_reference=reference,
        order=order,
        verified_event=successful_event(),
    )

    assert result.duplicate is True
    assert result.event is existing
    assert result.order_became_paid is False
    assert order.status == OrderStatus.awaiting_payment
    assert db.added == []


def test_success_requires_exact_order_amount() -> None:
    db = EventDatabase()
    order, reference = make_order_and_reference()

    with pytest.raises(PaymentEventError, match="amount"):
        apply_verified_payment_event(
            db,  # type: ignore[arg-type]
            payment_reference=reference,
            order=order,
            verified_event=successful_event(amount_minor=249999),
        )

    assert order.status == OrderStatus.awaiting_payment
    assert db.added == []


def test_success_requires_exact_order_currency() -> None:
    db = EventDatabase()
    order, reference = make_order_and_reference()

    with pytest.raises(PaymentEventError, match="currency"):
        apply_verified_payment_event(
            db,  # type: ignore[arg-type]
            payment_reference=reference,
            order=order,
            verified_event=successful_event(currency="EUR"),
        )

    assert order.status == OrderStatus.awaiting_payment


def test_verified_event_provider_must_match_checkout_reference() -> None:
    db = EventDatabase()
    order, reference = make_order_and_reference()

    with pytest.raises(PaymentEventError, match="provider"):
        apply_verified_payment_event(
            db,  # type: ignore[arg-type]
            payment_reference=reference,
            order=order,
            verified_event=successful_event(provider="different-gateway"),
        )


def test_late_failure_does_not_regress_successful_reference() -> None:
    db = EventDatabase()
    order, reference = make_order_and_reference()
    order.status = OrderStatus.paid
    reference.status = PaymentReferenceStatus.succeeded

    result = apply_verified_payment_event(
        db,  # type: ignore[arg-type]
        payment_reference=reference,
        order=order,
        verified_event=VerifiedPaymentEvent(
            provider=reference.provider,
            provider_event_id="event_late_failure",
            status=PaymentReferenceStatus.failed,
        ),
    )

    assert result.order_became_paid is False
    assert order.status == OrderStatus.paid
    assert reference.status == PaymentReferenceStatus.succeeded


def test_refund_event_is_recorded_without_inventing_refund_policy() -> None:
    db = EventDatabase()
    order, reference = make_order_and_reference()
    order.status = OrderStatus.paid
    reference.status = PaymentReferenceStatus.succeeded

    result = apply_verified_payment_event(
        db,  # type: ignore[arg-type]
        payment_reference=reference,
        order=order,
        verified_event=VerifiedPaymentEvent(
            provider=reference.provider,
            provider_event_id="event_refund",
            status=PaymentReferenceStatus.refunded,
            amount_minor=250000,
            currency="USD",
        ),
    )

    assert result.duplicate is False
    assert order.status == OrderStatus.paid
    assert reference.status == PaymentReferenceStatus.succeeded

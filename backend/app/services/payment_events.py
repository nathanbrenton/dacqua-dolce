from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.commerce import (
    Order,
    OrderStatus,
    PaymentProviderEvent,
    PaymentProviderReference,
    PaymentReferenceStatus,
)
from app.services.audit import record_audit_event
from app.services.payment_provider import PaymentMethodDisplay


class PaymentEventError(ValueError):
    pass


@dataclass(frozen=True)
class VerifiedPaymentEvent:
    """Provider event after gateway-specific authentication and normalization.

    This contract intentionally contains no raw webhook payload and no card
    data. The provider adapter is responsible for verifying signatures before
    constructing one of these events.
    """

    provider: str
    provider_event_id: str
    status: PaymentReferenceStatus
    amount_minor: int | None = None
    currency: str | None = None
    provider_payment_id: str | None = None
    provider_customer_id: str | None = None
    payment_method: PaymentMethodDisplay = field(
        default_factory=PaymentMethodDisplay
    )


@dataclass(frozen=True)
class PaymentEventApplyResult:
    event: PaymentProviderEvent
    duplicate: bool
    order_became_paid: bool


def _clean_identifier(
    value: str | None,
    *,
    field_name: str,
    max_length: int,
    required: bool = False,
) -> str | None:
    if value is None:
        if required:
            raise PaymentEventError(f"{field_name} is required.")
        return None

    normalized = value.strip()
    if not normalized:
        if required:
            raise PaymentEventError(f"{field_name} is required.")
        return None

    if len(normalized) > max_length:
        raise PaymentEventError(
            f"{field_name} exceeds the supported length."
        )

    return normalized


def _normalize_currency(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise PaymentEventError(
            "currency must be a three-letter alphabetic code."
        )

    return normalized


def _normalize_last4(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if len(normalized) != 4 or not normalized.isdigit():
        raise PaymentEventError(
            "payment method last4 must contain exactly four digits."
        )

    return normalized


def _copy_safe_reference_metadata(
    reference: PaymentProviderReference,
    *,
    provider_payment_id: str | None,
    provider_customer_id: str | None,
    payment_method_type: str | None,
    payment_method_brand: str | None,
    payment_method_last4: str | None,
) -> None:
    if provider_payment_id is not None:
        reference.provider_payment_id = provider_payment_id
    if provider_customer_id is not None:
        reference.provider_customer_id = provider_customer_id
    if payment_method_type is not None:
        reference.payment_method_type = payment_method_type
    if payment_method_brand is not None:
        reference.payment_method_brand = payment_method_brand
    if payment_method_last4 is not None:
        reference.payment_method_last4 = payment_method_last4


def apply_verified_payment_event(
    db: Session,
    *,
    payment_reference: PaymentProviderReference,
    order: Order,
    verified_event: VerifiedPaymentEvent,
) -> PaymentEventApplyResult:
    """Persist one authenticated normalized provider event idempotently.

    Only a verified successful payment is allowed to advance an order to paid.
    Failure/cancellation events remain retryable checkout outcomes. Refund order
    semantics are intentionally deferred until the provisioned gateway and the
    business refund workflow are commissioned.
    """

    if payment_reference.order_id != order.id:
        raise PaymentEventError(
            "Payment reference does not belong to the supplied order."
        )

    provider = _clean_identifier(
        verified_event.provider,
        field_name="provider",
        max_length=80,
        required=True,
    )
    event_id = _clean_identifier(
        verified_event.provider_event_id,
        field_name="provider_event_id",
        max_length=300,
        required=True,
    )
    assert provider is not None
    assert event_id is not None

    if provider != payment_reference.provider.strip():
        raise PaymentEventError(
            "Verified event provider does not match the payment reference."
        )

    existing = db.scalar(
        select(PaymentProviderEvent).where(
            PaymentProviderEvent.provider == provider,
            PaymentProviderEvent.provider_event_id == event_id,
        )
    )
    if existing is not None:
        if existing.payment_reference_id != payment_reference.id:
            raise PaymentEventError(
                "Provider event identifier is already bound to another "
                "payment reference."
            )
        return PaymentEventApplyResult(
            event=existing,
            duplicate=True,
            order_became_paid=False,
        )

    if verified_event.status == PaymentReferenceStatus.created:
        raise PaymentEventError(
            "Provider events cannot use the internal created status."
        )

    if (
        verified_event.amount_minor is not None
        and verified_event.amount_minor < 0
    ):
        raise PaymentEventError("amount_minor must not be negative.")

    currency = _normalize_currency(verified_event.currency)
    provider_payment_id = _clean_identifier(
        verified_event.provider_payment_id,
        field_name="provider_payment_id",
        max_length=300,
    )
    provider_customer_id = _clean_identifier(
        verified_event.provider_customer_id,
        field_name="provider_customer_id",
        max_length=300,
    )
    method_type = _clean_identifier(
        verified_event.payment_method.method_type,
        field_name="payment_method_type",
        max_length=80,
    )
    method_brand = _clean_identifier(
        verified_event.payment_method.brand,
        field_name="payment_method_brand",
        max_length=80,
    )
    method_last4 = _normalize_last4(
        verified_event.payment_method.last4
    )

    order_became_paid = False

    if verified_event.status == PaymentReferenceStatus.succeeded:
        if payment_reference.status == PaymentReferenceStatus.refunded:
            raise PaymentEventError(
                "Successful payment cannot reopen a refunded payment reference."
            )
        if verified_event.amount_minor is None or currency is None:
            raise PaymentEventError(
                "Successful payment events require amount and currency."
            )
        if verified_event.amount_minor != order.total_amount_minor:
            raise PaymentEventError(
                "Successful payment amount does not match the order total."
            )
        if currency != order.currency.upper():
            raise PaymentEventError(
                "Successful payment currency does not match the order."
            )
        if order.status == OrderStatus.awaiting_payment:
            order.status = OrderStatus.paid
            order_became_paid = True
        elif order.status not in {
            OrderStatus.paid,
            OrderStatus.processing,
            OrderStatus.shipped,
            OrderStatus.delivered,
        }:
            raise PaymentEventError(
                "Successful payment cannot be applied to this order status."
            )

        if payment_reference.status != PaymentReferenceStatus.refunded:
            payment_reference.status = PaymentReferenceStatus.succeeded
    elif verified_event.status in {
        PaymentReferenceStatus.pending,
        PaymentReferenceStatus.failed,
        PaymentReferenceStatus.cancelled,
    }:
        if payment_reference.status not in {
            PaymentReferenceStatus.succeeded,
            PaymentReferenceStatus.refunded,
        }:
            payment_reference.status = verified_event.status
    elif verified_event.status == PaymentReferenceStatus.refunded:
        # The event is retained, but PT20.2A intentionally does not infer full
        # versus partial refund semantics or mutate the order/ref status.
        pass

    _copy_safe_reference_metadata(
        payment_reference,
        provider_payment_id=provider_payment_id,
        provider_customer_id=provider_customer_id,
        payment_method_type=method_type,
        payment_method_brand=method_brand,
        payment_method_last4=method_last4,
    )

    event = PaymentProviderEvent(
        payment_reference_id=payment_reference.id,
        provider=provider,
        provider_event_id=event_id,
        status=verified_event.status,
        amount_minor=verified_event.amount_minor,
        currency=currency,
        provider_payment_id=provider_payment_id,
        provider_customer_id=provider_customer_id,
        payment_method_type=method_type,
        payment_method_brand=method_brand,
        payment_method_last4=method_last4,
    )
    db.add(event)

    record_audit_event(
        db,
        action="payment.provider_event_applied",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=None,
        metadata={
            "provider": provider,
            "provider_event_id": event_id,
            "payment_reference_id": str(payment_reference.id),
            "status": verified_event.status.value,
            "order_became_paid": order_became_paid,
        },
    )
    db.flush()

    return PaymentEventApplyResult(
        event=event,
        duplicate=False,
        order_became_paid=order_became_paid,
    )

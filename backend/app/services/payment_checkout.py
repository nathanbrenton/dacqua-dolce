from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.sales_area import (
    SalesAreaEligibilityError,
    SalesAreaPolicy,
    require_delivery_address_in_sales_area,
)
from app.models.commerce import (
    Order,
    OrderStatus,
    PaymentProviderReference,
    PaymentReferenceStatus,
)
from app.services.audit import record_audit_event
from app.services.cancellations import get_order_cancellation_request
from app.services.payment_provider import (
    CheckoutSessionRequest,
    PaymentProviderAdapter,
)


class PaymentCheckoutError(ValueError):
    pass


@dataclass(frozen=True)
class HostedCheckout:
    provider: str
    checkout_session_id: str
    redirect_url: str
    payment_reference: PaymentProviderReference


def _require_https_redirect(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise PaymentCheckoutError(
            "Payment provider returned an invalid hosted-checkout URL."
        )


def begin_hosted_checkout(
    db: Session,
    *,
    order: Order,
    customer_email: str,
    success_url: str,
    cancel_url: str,
    provider: PaymentProviderAdapter,
    sales_area_policy: SalesAreaPolicy | None = None,
) -> HostedCheckout:
    """Create a provider-hosted checkout without handling card data.

    This orchestration layer is intentionally provider-neutral. PT20.1 tests
    it with a fake adapter; production wiring waits until Affinity24 confirms
    the concrete gateway and supplies its authoritative integration contract.
    """

    if order.status != OrderStatus.awaiting_payment:
        raise PaymentCheckoutError(
            "Only an order awaiting payment can start hosted checkout."
        )

    cancellation = get_order_cancellation_request(
        db,
        order_id=order.id,
    )
    if (
        cancellation is not None
        and cancellation.status != "declined"
    ):
        raise PaymentCheckoutError(
            "Hosted checkout is unavailable while a cancellation request is active."
        )

    try:
        require_delivery_address_in_sales_area(
            order.delivery_address_snapshot,
            policy=sales_area_policy,
        )
    except SalesAreaEligibilityError as exc:
        raise PaymentCheckoutError(str(exc)) from exc

    result = provider.create_checkout_session(
        CheckoutSessionRequest(
            order_id=order.id,
            amount_minor=order.total_amount_minor,
            currency=order.currency,
            customer_email=customer_email,
            success_url=success_url,
            cancel_url=cancel_url,
            idempotency_key=f"order:{order.id}:hosted-checkout",
        )
    )

    provider_name = result.provider.strip()
    checkout_id = result.checkout_session_id.strip()
    if not provider_name or not checkout_id:
        raise PaymentCheckoutError(
            "Payment provider did not return a durable checkout reference."
        )
    _require_https_redirect(result.redirect_url)

    payment_reference = db.scalar(
        select(PaymentProviderReference).where(
            PaymentProviderReference.provider == provider_name,
            PaymentProviderReference.provider_checkout_id == checkout_id,
        )
    )

    if payment_reference is None:
        payment_reference = PaymentProviderReference(
            order_id=order.id,
            provider=provider_name,
            provider_checkout_id=checkout_id,
            status=PaymentReferenceStatus.pending,
        )
        db.add(payment_reference)
        db.flush()
    elif payment_reference.order_id != order.id:
        raise PaymentCheckoutError(
            "Payment provider checkout reference is already bound to another order."
        )

    record_audit_event(
        db,
        action="payment.hosted_checkout_created",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=order.user_id,
        metadata={
            "provider": provider_name,
            "provider_checkout_id": checkout_id,
            "payment_reference_id": str(payment_reference.id),
        },
    )
    db.flush()

    return HostedCheckout(
        provider=provider_name,
        checkout_session_id=checkout_id,
        redirect_url=result.redirect_url,
        payment_reference=payment_reference,
    )

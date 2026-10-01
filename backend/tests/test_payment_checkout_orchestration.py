import uuid

import pytest

from app.models.commerce import (
    Order,
    OrderCancellationRequest,
    OrderStatus,
    PaymentProviderReference,
)
from app.services.payment_checkout import PaymentCheckoutError, begin_hosted_checkout
from app.services.payment_provider import CheckoutSessionResult


class FakeProvider:
    def __init__(self) -> None:
        self.request = None

    def create_checkout_session(self, request):
        self.request = request
        return CheckoutSessionResult(
            provider="sandbox-gateway",
            checkout_session_id="checkout_123",
            redirect_url="https://payments.example.test/checkout_123",
        )


class CheckoutDatabase:
    def __init__(
        self,
        cancellation: OrderCancellationRequest | None = None,
    ) -> None:
        self.added: list[object] = []
        self.cancellation = cancellation

    def scalar(self, statement: object):
        query = str(statement)
        if "FROM order_cancellation_requests" in query:
            return self.cancellation
        if "FROM payment_provider_references" in query:
            return None
        raise AssertionError(query)

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        for value in self.added:
            if getattr(value, "id", None) is None and hasattr(value, "id"):
                value.id = uuid.uuid4()


def test_hosted_checkout_passes_only_safe_order_context() -> None:
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=240000,
        charges_amount_minor=10000,
        total_amount_minor=250000,
        currency="USD",
    )
    db = CheckoutDatabase()
    provider = FakeProvider()

    result = begin_hosted_checkout(
        db,  # type: ignore[arg-type]
        order=order,
        customer_email="customer@example.com",
        success_url="https://dacquadolce.com/account?payment=success",
        cancel_url="https://dacquadolce.com/account?payment=cancelled",
        provider=provider,
    )

    assert result.redirect_url.startswith("https://")
    assert provider.request is not None
    assert provider.request.order_id == order.id
    assert provider.request.amount_minor == 250000
    assert provider.request.idempotency_key == f"order:{order.id}:hosted-checkout"
    refs = [value for value in db.added if isinstance(value, PaymentProviderReference)]
    assert len(refs) == 1
    assert refs[0].provider_checkout_id == "checkout_123"


def test_hosted_checkout_rejects_non_payment_order() -> None:
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.paid,
        subtotal_amount_minor=250000,
        charges_amount_minor=0,
        total_amount_minor=250000,
        currency="USD",
    )

    with pytest.raises(PaymentCheckoutError):
        begin_hosted_checkout(
            CheckoutDatabase(),  # type: ignore[arg-type]
            order=order,
            customer_email="customer@example.com",
            success_url="https://dacquadolce.com/account",
            cancel_url="https://dacquadolce.com/account",
            provider=FakeProvider(),
        )


def test_hosted_checkout_is_blocked_by_active_cancellation() -> None:
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=250000,
        charges_amount_minor=0,
        total_amount_minor=250000,
        currency="USD",
    )
    cancellation = OrderCancellationRequest(
        id=uuid.uuid4(),
        order_id=order.id,
        requested_by_user_id=order.user_id,
        eligibility_mode="unrestricted",
        status="approved",
    )
    provider = FakeProvider()

    with pytest.raises(PaymentCheckoutError, match="cancellation"):
        begin_hosted_checkout(
            CheckoutDatabase(cancellation),  # type: ignore[arg-type]
            order=order,
            customer_email="customer@example.com",
            success_url="https://dacquadolce.com/account",
            cancel_url="https://dacquadolce.com/account",
            provider=provider,
        )

    assert provider.request is None

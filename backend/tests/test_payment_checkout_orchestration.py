import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.sales_area import SalesAreaPolicy
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
        *,
        tax_calculation: object | None = ...,
    ) -> None:
        self.added: list[object] = []
        self.cancellation = cancellation
        self.tax_calculation = (
            SimpleNamespace(
                livemode=False,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                committed_at=None,
                amount_total_minor=250000,
                currency="USD",
            )
            if tax_calculation is ...
            else tax_calculation
        )

    def scalar(self, statement: object):
        query = str(statement)
        if "FROM order_cancellation_requests" in query:
            return self.cancellation
        if "FROM tax_calculations" in query:
            return self.tax_calculation
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
        delivery_address_snapshot={
            "recipient_name": "Customer",
            "line1": "123 Main St",
            "city": "Irvine",
            "region_code": "CA",
            "postal_code": "92614",
            "country_code": "US",
        },
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


def test_hosted_checkout_rejects_missing_delivery_address_when_enforced() -> None:
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=250000,
        charges_amount_minor=0,
        total_amount_minor=250000,
        currency="USD",
    )
    provider = FakeProvider()

    with pytest.raises(
        PaymentCheckoutError,
        match="delivery address is required",
    ):
        begin_hosted_checkout(
            CheckoutDatabase(),  # type: ignore[arg-type]
            order=order,
            customer_email="customer@example.com",
            success_url="https://dacquadolce.com/account",
            cancel_url="https://dacquadolce.com/account",
            provider=provider,
        )

    assert provider.request is None


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


def test_hosted_checkout_rejects_out_of_area_delivery_address() -> None:
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=250000,
        charges_amount_minor=0,
        total_amount_minor=250000,
        currency="USD",
        delivery_address_snapshot={
            "recipient_name": "Customer",
            "line1": "123 Desert Rd",
            "city": "Las Vegas",
            "region_code": "NV",
            "postal_code": "89101",
            "country_code": "US",
        },
    )
    provider = FakeProvider()
    policy = SalesAreaPolicy(
        mode="allowlist",
        country_code="US",
        region_codes=frozenset({"CA"}),
        label="Launch delivery area",
    )

    with pytest.raises(
        PaymentCheckoutError,
        match="outside Launch delivery area",
    ):
        begin_hosted_checkout(
            CheckoutDatabase(),  # type: ignore[arg-type]
            order=order,
            customer_email="customer@example.com",
            success_url="https://dacquadolce.com/account",
            cancel_url="https://dacquadolce.com/account",
            provider=provider,
            sales_area_policy=policy,
        )

    assert provider.request is None


def test_hosted_checkout_requires_authoritative_tax_calculation() -> None:
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=250000,
        charges_amount_minor=0,
        total_amount_minor=250000,
        currency="USD",
        delivery_address_snapshot={
            "recipient_name": "Customer",
            "line1": "123 Main St",
            "city": "Irvine",
            "region_code": "CA",
            "postal_code": "92614",
            "country_code": "US",
        },
    )
    provider = FakeProvider()

    with pytest.raises(
        PaymentCheckoutError,
        match="automated tax must be recalculated",
    ):
        begin_hosted_checkout(
            CheckoutDatabase(tax_calculation=None),  # type: ignore[arg-type]
            order=order,
            customer_email="customer@example.com",
            success_url="https://dacquadolce.com/account",
            cancel_url="https://dacquadolce.com/account",
            provider=provider,
        )

    assert provider.request is None

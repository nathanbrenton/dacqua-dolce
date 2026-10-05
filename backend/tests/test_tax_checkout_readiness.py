import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.models.commerce import Order, OrderStatus
from app.services import tax_automation


class CalculationDatabase:
    def __init__(self, calculation: object) -> None:
        self.calculation = calculation

    def scalar(self, _statement: object) -> object:
        return self.calculation


def awaiting_payment_order() -> Order:
    return Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=10000,
        charges_amount_minor=800,
        total_amount_minor=10800,
        currency="USD",
    )


def current_sandbox_calculation() -> SimpleNamespace:
    return SimpleNamespace(
        livemode=False,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        committed_at=None,
        amount_total_minor=10800,
        currency="USD",
    )


def test_sandbox_tax_can_support_nonproduction_checkout_boundary(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        tax_automation,
        "get_settings",
        lambda: SimpleNamespace(is_production=False),
    )
    calculation = current_sandbox_calculation()

    result = tax_automation.require_order_tax_ready(
        CalculationDatabase(calculation),  # type: ignore[arg-type]
        order=awaiting_payment_order(),
    )

    assert result is calculation


def test_sandbox_tax_cannot_authorize_production_checkout(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        tax_automation,
        "get_settings",
        lambda: SimpleNamespace(is_production=True),
    )

    with pytest.raises(
        tax_automation.TaxCheckoutReadinessError,
        match="cannot authorize production checkout",
    ):
        tax_automation.require_order_tax_ready(
            CalculationDatabase(current_sandbox_calculation()),  # type: ignore[arg-type]
            order=awaiting_payment_order(),
        )

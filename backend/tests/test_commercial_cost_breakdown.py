from types import SimpleNamespace

import pytest

from app.services.commercial_costs import commercial_cost_breakdown


def charge(kind: str, amount_minor: int) -> SimpleNamespace:
    return SimpleNamespace(kind=kind, amount_minor=amount_minor)


def test_breakdown_maps_commercial_adjustments_to_launch_buckets() -> None:
    breakdown = commercial_cost_breakdown(
        subtotal_amount_minor=250000,
        charges=[
            charge("shipping", 25000),
            charge("shipping_insurance", 3500),
            charge("tax", 18750),
            charge("installation", 50000),
            charge("discount", -10000),
            charge("other_charge", 2500),
            charge("other_credit", -1000),
        ],
        expected_total_amount_minor=338750,
    )

    assert breakdown.product_other_amount_minor == 291500
    assert breakdown.shipping_delivery_amount_minor == 25000
    assert breakdown.shipping_insurance_amount_minor == 3500
    assert breakdown.tax_amount_minor == 18750
    assert breakdown.total_amount_minor == 338750


def test_historical_quote_without_shipping_insurance_derives_zero_bucket() -> None:
    breakdown = commercial_cost_breakdown(
        subtotal_amount_minor=125000,
        charges=[
            charge("shipping", 12000),
            charge("tax", 9000),
        ],
        expected_total_amount_minor=146000,
    )

    assert breakdown.shipping_insurance_amount_minor == 0
    assert breakdown.total_amount_minor == 146000


def test_breakdown_rejects_unknown_charge_kind() -> None:
    with pytest.raises(ValueError, match="Unsupported commercial charge kind"):
        commercial_cost_breakdown(
            subtotal_amount_minor=10000,
            charges=[charge("mystery", 100)],
        )


def test_breakdown_rejects_stored_total_drift() -> None:
    with pytest.raises(ValueError, match="does not match the stored total"):
        commercial_cost_breakdown(
            subtotal_amount_minor=10000,
            charges=[charge("shipping", 1000)],
            expected_total_amount_minor=10999,
        )

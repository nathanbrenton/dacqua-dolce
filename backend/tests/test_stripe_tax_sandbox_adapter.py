from datetime import UTC, datetime

import pytest

from app.services.stripe_tax import StripeTaxError, StripeTaxSandboxAdapter
from app.services.tax_provider import (
    TaxAddress,
    TaxCalculationRequest,
    TaxLineItem,
)


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def calculation_request() -> TaxCalculationRequest:
    return TaxCalculationRequest(
        currency="USD",
        customer_address=TaxAddress(
            line1="123 Main St",
            city="Irvine",
            region_code="CA",
            postal_code="92614",
            country_code="US",
        ),
        line_items=(
            TaxLineItem(
                reference="SKU-1",
                amount_minor=10000,
                quantity=2,
                tax_code="txcd_reviewed",
            ),
        ),
        shipping_amount_minor=1500,
        idempotency_key="order:test:tax-calculation",
    )


def test_stripe_tax_sandbox_calculation_is_tax_exclusive_and_sanitized() -> None:
    captured: dict[str, object] = {}

    def post(url, *, data, headers, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "id": "taxcalc_test",
                "livemode": False,
                "currency": "usd",
                "amount_total": 12350,
                "tax_amount_exclusive": 850,
                "tax_amount_inclusive": 0,
                "expires_at": 1791220000,
                "line_items": {
                    "data": [
                        {
                            "reference": "SKU-1",
                            "amount": 10000,
                            "amount_tax": 800,
                            "quantity": 2,
                            "tax_code": "txcd_reviewed",
                            "tax_behavior": "exclusive",
                            "ignored": "not persisted",
                        }
                    ]
                },
                "shipping_cost": {
                    "amount": 1500,
                    "amount_tax": 50,
                },
                "tax_breakdown": [
                    {
                        "amount": 850,
                        "taxable_amount": 11500,
                        "taxability_reason": "standard_rated",
                        "tax_rate_details": {
                            "country": "US",
                            "state": "CA",
                            "tax_type": "sales_tax",
                            "percentage_decimal": "7.39",
                            "ignored": "not persisted",
                        },
                    }
                ],
                "raw_secretish_field": "discard me",
            }
        )

    adapter = StripeTaxSandboxAdapter(
        secret_key="sk_test_example",
        post=post,
    )
    result = adapter.calculate(calculation_request())

    assert captured["url"] == "https://api.stripe.com/v1/tax/calculations"
    assert ("line_items[0][tax_behavior]", "exclusive") in captured["data"]
    assert ("shipping_cost[tax_behavior]", "exclusive") in captured["data"]
    assert ("customer_details[address_source]", "shipping") in captured["data"]
    assert captured["headers"]["Idempotency-Key"] == "order:test:tax-calculation"
    assert result.provider_calculation_id == "taxcalc_test"
    assert result.tax_amount_minor == 850
    assert result.amount_total_minor == 12350
    assert result.livemode is False
    assert result.line_items[0]["reference"] == "SKU-1"
    assert "ignored" not in result.line_items[0]
    assert "ignored" not in result.tax_breakdown[0]


def test_stripe_tax_sandbox_refuses_live_response() -> None:
    def post(_url, *, data, headers, timeout):
        return FakeResponse({"livemode": True})

    adapter = StripeTaxSandboxAdapter(
        secret_key="sk_test_example",
        post=post,
    )
    with pytest.raises(StripeTaxError, match="live-mode"):
        adapter.calculate(calculation_request())


def test_stripe_tax_sandbox_refuses_live_key() -> None:
    with pytest.raises(StripeTaxError, match="test-mode"):
        StripeTaxSandboxAdapter(secret_key="sk_live_nope")


def test_stripe_tax_transaction_from_calculation() -> None:
    captured: dict[str, object] = {}

    def post(url, *, data, headers, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["headers"] = headers
        return FakeResponse(
            {
                "id": "tax_test_transaction",
                "reference": "dacqua-order:abc",
                "currency": "usd",
                "livemode": False,
                "posted_at": int(datetime.now(UTC).timestamp()),
                "tax_date": int(datetime.now(UTC).timestamp()),
                "line_items": {
                    "data": [
                        {
                            "reference": "SKU-1",
                            "amount": 10000,
                            "amount_tax": 800,
                            "quantity": 2,
                            "tax_code": "txcd_reviewed",
                            "tax_behavior": "exclusive",
                        }
                    ]
                },
                "shipping_cost": {
                    "amount": 1500,
                    "amount_tax": 50,
                    "tax_code": "txcd_92010001",
                    "tax_behavior": "exclusive",
                },
            }
        )

    adapter = StripeTaxSandboxAdapter(
        secret_key="rk_test_example",
        post=post,
    )
    result = adapter.create_transaction_from_calculation(
        provider_calculation_id="taxcalc_test",
        reference="dacqua-order:abc",
        idempotency_key="order:abc:tax-transaction",
    )

    assert captured["url"].endswith("/tax/transactions/create_from_calculation")
    assert ("calculation", "taxcalc_test") in captured["data"]
    assert result.tax_amount_minor == 850
    assert result.amount_total_minor == 12350
    assert result.provider_reference == "dacqua-order:abc"
    assert result.livemode is False

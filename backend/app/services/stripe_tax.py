from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from app.services.tax_provider import (
    TaxCalculationRequest,
    TaxCalculationResult,
    TaxTransactionResult,
)

STRIPE_TAX_API_BASE = "https://api.stripe.com/v1"


class StripeTaxError(ValueError):
    pass


def _as_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise StripeTaxError(f"Stripe Tax response is missing a valid {key}.")
    return value


def _as_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StripeTaxError(f"Stripe Tax response is missing a valid {key}.")
    return value.strip()


def _sanitized_tax_breakdown(payload: dict[str, Any]) -> tuple[dict[str, object], ...]:
    result: list[dict[str, object]] = []
    raw = payload.get("tax_breakdown")
    if not isinstance(raw, list):
        return ()

    for entry in raw:
        if not isinstance(entry, dict):
            continue
        rate = entry.get("tax_rate_details")
        rate_details = rate if isinstance(rate, dict) else {}
        result.append(
            {
                "amount": entry.get("amount"),
                "taxable_amount": entry.get("taxable_amount"),
                "taxability_reason": entry.get("taxability_reason"),
                "country": rate_details.get("country"),
                "state": rate_details.get("state"),
                "tax_type": rate_details.get("tax_type"),
                "percentage_decimal": rate_details.get("percentage_decimal"),
            }
        )
    return tuple(result)


def _sanitized_line_items(payload: dict[str, Any]) -> tuple[dict[str, object], ...]:
    container = payload.get("line_items")
    if not isinstance(container, dict):
        return ()
    raw = container.get("data")
    if not isinstance(raw, list):
        return ()

    result: list[dict[str, object]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        result.append(
            {
                "reference": entry.get("reference"),
                "amount": entry.get("amount"),
                "amount_tax": entry.get("amount_tax"),
                "quantity": entry.get("quantity"),
                "tax_code": entry.get("tax_code"),
                "tax_behavior": entry.get("tax_behavior"),
            }
        )
    return tuple(result)


class StripeTaxSandboxAdapter:
    provider_name = "stripe_tax"

    def __init__(
        self,
        *,
        secret_key: str,
        post: Callable[..., httpx.Response] | None = None,
    ) -> None:
        normalized = secret_key.strip()
        if not normalized.startswith(("sk_test_", "rk_test_")):
            raise StripeTaxError(
                "PT44 Stripe Tax adapter accepts test-mode credentials only."
            )
        self._secret_key = normalized
        self._post = post or httpx.post

    def _request(
        self,
        path: str,
        *,
        data: list[tuple[str, str]],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._secret_key}",
        }
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        try:
            response = self._post(
                f"{STRIPE_TAX_API_BASE}{path}",
                data=data,
                headers=headers,
                timeout=15.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise StripeTaxError(
                "Stripe Tax sandbox request failed. "
                "No tax amount was applied."
            ) from exc

        if not isinstance(payload, dict):
            raise StripeTaxError("Stripe Tax returned an unexpected response.")

        if payload.get("livemode") is not False:
            raise StripeTaxError(
                "Stripe Tax sandbox adapter refused a live-mode response."
            )
        return payload

    def calculate(
        self,
        request: TaxCalculationRequest,
    ) -> TaxCalculationResult:
        if not request.line_items:
            raise StripeTaxError("At least one tax line item is required.")
        if request.shipping_amount_minor < 0:
            raise StripeTaxError("Shipping amount cannot be negative.")

        data: list[tuple[str, str]] = [
            ("currency", request.currency.lower()),
            (
                "customer_details[address][line1]",
                request.customer_address.line1,
            ),
            (
                "customer_details[address][city]",
                request.customer_address.city,
            ),
            (
                "customer_details[address][state]",
                request.customer_address.region_code,
            ),
            (
                "customer_details[address][postal_code]",
                request.customer_address.postal_code,
            ),
            (
                "customer_details[address][country]",
                request.customer_address.country_code,
            ),
            ("customer_details[address_source]", "shipping"),
        ]
        if request.customer_address.line2:
            data.append(
                (
                    "customer_details[address][line2]",
                    request.customer_address.line2,
                )
            )

        for index, item in enumerate(request.line_items):
            if item.amount_minor < 0 or item.quantity <= 0:
                raise StripeTaxError("Tax line items must be positive.")
            prefix = f"line_items[{index}]"
            data.extend(
                [
                    (f"{prefix}[amount]", str(item.amount_minor)),
                    (f"{prefix}[quantity]", str(item.quantity)),
                    (f"{prefix}[tax_code]", item.tax_code),
                    (f"{prefix}[reference]", item.reference),
                    (f"{prefix}[tax_behavior]", "exclusive"),
                ]
            )

        if request.shipping_amount_minor > 0:
            data.extend(
                [
                    (
                        "shipping_cost[amount]",
                        str(request.shipping_amount_minor),
                    ),
                    ("shipping_cost[tax_behavior]", "exclusive"),
                ]
            )

        data.append(("expand[0]", "line_items"))
        payload = self._request(
            "/tax/calculations",
            data=data,
            idempotency_key=request.idempotency_key,
        )

        tax_exclusive = _as_int(payload, "tax_amount_exclusive")
        tax_inclusive = _as_int(payload, "tax_amount_inclusive")
        if tax_inclusive != 0:
            raise StripeTaxError(
                "D'Acqua Dolce PT44 expects tax-exclusive pricing."
            )

        expires_raw = payload.get("expires_at")
        expires_at = (
            datetime.fromtimestamp(expires_raw, tz=UTC)
            if isinstance(expires_raw, int)
            else None
        )
        currency = _as_str(payload, "currency").upper()
        expected_line_amount = sum(
            item.amount_minor
            for item in request.line_items
        )
        amount_total = _as_int(payload, "amount_total")
        expected_total = (
            expected_line_amount
            + request.shipping_amount_minor
            + tax_exclusive
        )
        if amount_total != expected_total:
            raise StripeTaxError(
                "Stripe Tax calculation total does not match the submitted "
                "tax-exclusive merchandise and shipping amounts."
            )

        return TaxCalculationResult(
            provider=self.provider_name,
            provider_calculation_id=_as_str(payload, "id"),
            currency=currency,
            line_items_amount_minor=expected_line_amount,
            shipping_amount_minor=request.shipping_amount_minor,
            tax_amount_minor=tax_exclusive,
            amount_total_minor=amount_total,
            expires_at=expires_at,
            livemode=False,
            line_items=_sanitized_line_items(payload),
            tax_breakdown=_sanitized_tax_breakdown(payload),
        )

    def create_transaction_from_calculation(
        self,
        *,
        provider_calculation_id: str,
        reference: str,
        idempotency_key: str,
    ) -> TaxTransactionResult:
        payload = self._request(
            "/tax/transactions/create_from_calculation",
            data=[
                ("calculation", provider_calculation_id),
                ("reference", reference),
                ("expand[0]", "line_items"),
            ],
            idempotency_key=idempotency_key,
        )

        line_items = _sanitized_line_items(payload)
        tax_amount = sum(
            int(item.get("amount_tax") or 0)
            for item in line_items
        )
        shipping = payload.get("shipping_cost")
        if isinstance(shipping, dict):
            shipping_tax = shipping.get("amount_tax")
            if isinstance(shipping_tax, int):
                tax_amount += shipping_tax

        line_amount = sum(
            int(item.get("amount") or 0)
            for item in line_items
        )
        shipping_amount = 0
        if isinstance(shipping, dict):
            raw_shipping_amount = shipping.get("amount")
            if isinstance(raw_shipping_amount, int):
                shipping_amount = raw_shipping_amount

        return TaxTransactionResult(
            provider=self.provider_name,
            provider_transaction_id=_as_str(payload, "id"),
            provider_reference=_as_str(payload, "reference"),
            currency=_as_str(payload, "currency").upper(),
            tax_amount_minor=tax_amount,
            amount_total_minor=line_amount + shipping_amount + tax_amount,
            livemode=False,
            response_summary={
                "posted_at": payload.get("posted_at"),
                "tax_date": payload.get("tax_date"),
                "line_items": list(line_items),
                "shipping_cost": (
                    {
                        "amount": shipping.get("amount"),
                        "amount_tax": shipping.get("amount_tax"),
                        "tax_code": shipping.get("tax_code"),
                        "tax_behavior": shipping.get("tax_behavior"),
                    }
                    if isinstance(shipping, dict)
                    else None
                ),
            },
        )

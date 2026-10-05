from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class TaxAddress:
    line1: str
    city: str
    region_code: str
    postal_code: str
    country_code: str
    line2: str | None = None


@dataclass(frozen=True)
class TaxLineItem:
    reference: str
    amount_minor: int
    quantity: int
    tax_code: str


@dataclass(frozen=True)
class TaxCalculationRequest:
    currency: str
    customer_address: TaxAddress
    line_items: tuple[TaxLineItem, ...]
    shipping_amount_minor: int = 0
    idempotency_key: str | None = None


@dataclass(frozen=True)
class TaxCalculationResult:
    provider: str
    provider_calculation_id: str
    currency: str
    line_items_amount_minor: int
    shipping_amount_minor: int
    tax_amount_minor: int
    amount_total_minor: int
    expires_at: datetime | None
    livemode: bool
    line_items: tuple[dict[str, object], ...] = field(default_factory=tuple)
    tax_breakdown: tuple[dict[str, object], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaxTransactionResult:
    provider: str
    provider_transaction_id: str
    provider_reference: str
    currency: str
    tax_amount_minor: int
    amount_total_minor: int
    livemode: bool
    response_summary: dict[str, object] = field(default_factory=dict)


class TaxProviderAdapter(Protocol):
    provider_name: str

    def calculate(
        self,
        request: TaxCalculationRequest,
    ) -> TaxCalculationResult:
        ...

    def create_transaction_from_calculation(
        self,
        *,
        provider_calculation_id: str,
        reference: str,
        idempotency_key: str,
    ) -> TaxTransactionResult:
        ...

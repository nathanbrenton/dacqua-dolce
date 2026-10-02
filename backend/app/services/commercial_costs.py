from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from app.models.quote import CommercialChargeKind


class CommercialChargeLike(Protocol):
    kind: str
    amount_minor: int


@dataclass(frozen=True)
class CommercialCostBreakdown:
    product_other_amount_minor: int
    shipping_delivery_amount_minor: int
    shipping_insurance_amount_minor: int
    tax_amount_minor: int
    total_amount_minor: int

    def as_dict(self) -> dict[str, int]:
        return {
            "product_other_amount_minor": self.product_other_amount_minor,
            "shipping_delivery_amount_minor": self.shipping_delivery_amount_minor,
            "shipping_insurance_amount_minor": self.shipping_insurance_amount_minor,
            "tax_amount_minor": self.tax_amount_minor,
            "total_amount_minor": self.total_amount_minor,
        }


_PRODUCT_OTHER_KINDS = {
    CommercialChargeKind.installation.value,
    CommercialChargeKind.discount.value,
    CommercialChargeKind.other_charge.value,
    CommercialChargeKind.other_credit.value,
}
_KNOWN_KINDS = _PRODUCT_OTHER_KINDS | {
    CommercialChargeKind.shipping.value,
    CommercialChargeKind.shipping_insurance.value,
    CommercialChargeKind.tax.value,
}


def commercial_cost_breakdown(
    *,
    subtotal_amount_minor: int,
    charges: Iterable[CommercialChargeLike],
    expected_total_amount_minor: int | None = None,
) -> CommercialCostBreakdown:
    product_other = subtotal_amount_minor
    shipping_delivery = 0
    shipping_insurance = 0
    tax = 0

    for charge in charges:
        if charge.kind not in _KNOWN_KINDS:
            raise ValueError(f"Unsupported commercial charge kind: {charge.kind}")

        if charge.kind == CommercialChargeKind.shipping.value:
            shipping_delivery += charge.amount_minor
        elif charge.kind == CommercialChargeKind.shipping_insurance.value:
            shipping_insurance += charge.amount_minor
        elif charge.kind == CommercialChargeKind.tax.value:
            tax += charge.amount_minor
        else:
            product_other += charge.amount_minor

    total = product_other + shipping_delivery + shipping_insurance + tax
    if expected_total_amount_minor is not None and total != expected_total_amount_minor:
        raise ValueError("Commercial cost breakdown does not match the stored total.")

    return CommercialCostBreakdown(
        product_other_amount_minor=product_other,
        shipping_delivery_amount_minor=shipping_delivery,
        shipping_insurance_amount_minor=shipping_insurance,
        tax_amount_minor=tax,
        total_amount_minor=total,
    )

"""Pending Pureline option review records. NOT a price or fitment authority.

Only owner-supplied descriptive cartridge choices are indexed. To authorize a
particular manufacturer model, housing combination, inventory product or price,
a later reviewed catalog migration and explicit commercial approval is needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Literal

from app.schemas.product_configuration import CARTRIDGE_CHOICES

REVIEW_FILE = Path(__file__).resolve().parents[2] / "catalog" / "pureline_cartridge_review.json"
_FIELDS = frozenset({
    "category", "requested_description", "manufacturer", "manufacturer_model",
    "supplier_part_number", "compatible_housing_models", "approved_positions",
    "supplier_cost_usd", "authorized_unit_price_usd", "currency",
    "fitment_evidence", "price_approval_reference", "approval_status",
})
_UNAPPROVED = (
    "manufacturer", "manufacturer_model", "supplier_part_number", "supplier_cost_usd",
    "authorized_unit_price_usd", "currency", "fitment_evidence", "price_approval_reference",
)


@dataclass(frozen=True, slots=True)
class PendingCartridgeReview:
    """A review identity, not an approved or purchasable product."""

    category: Literal["sediment", "carbon", "iron"]
    requested_description: str
    nominal_housing_length_inches: int = 20
    manufacturer: None = None
    manufacturer_model: None = None
    supplier_part_number: None = None
    supplier_cost_usd: None = None
    authorized_unit_price_usd: None = None
    currency: None = None
    approved_positions: tuple[int, ...] = ()
    compatible_housing_models: tuple[str, ...] = ()
    fitment_evidence: None = None
    price_approval_reference: None = None
    approval_status: Literal["pending"] = "pending"

    @property
    def staff_review_required(self) -> bool:
        return True


@lru_cache(maxsize=1)
def load_pending_pureline_reviews() -> dict[tuple[str, str], PendingCartridgeReview]:
    """Load a complete, fail-closed review register; never return prices.

    File omissions, unexpected entries, or any attempted approval of a pending
    record reject the entire register. The JSON is deliberately not a pathway
    for independently activating commercial options.
    """
    raw = json.loads(REVIEW_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "scope", "nominal_housing_length_inches", "entries",
    }:
        raise ValueError("Invalid Pureline review registry structure")
    if (raw["schema_version"] != 1 or raw["scope"] != "pending_review_only"
            or raw["nominal_housing_length_inches"] != 20
            or not isinstance(raw["entries"], list)):
        raise ValueError("Unsupported Pureline review registry metadata")

    records: dict[tuple[str, str], PendingCartridgeReview] = {}
    for entry in raw["entries"]:
        if not isinstance(entry, dict) or set(entry) != _FIELDS:
            raise ValueError("Unexpected Pureline option review fields")
        category = entry["category"]
        label = entry["requested_description"]
        if (not isinstance(category, str) or not isinstance(label, str)
                or label not in CARTRIDGE_CHOICES.get(category, ())):
            raise ValueError("Unknown Pureline descriptive option")
        key = (category, label)
        if key in records:
            raise ValueError("Duplicate Pureline descriptive option")
        if entry["approval_status"] != "pending":
            raise ValueError("Pureline option approval requires a separately reviewed milestone")
        if any(entry[field] is not None for field in _UNAPPROVED):
            raise ValueError("Unapproved Pureline options cannot have supplier/price evidence")
        if (entry["approved_positions"] != []
                or entry["compatible_housing_models"] != []):
            raise ValueError("No Pureline housing fitments have been approved")
        records[key] = PendingCartridgeReview(category=category, requested_description=label)

    expected = {(category, name)
                for category, choices in CARTRIDGE_CHOICES.items()
                for name in choices}
    if set(records) != expected:
        raise ValueError("Pureline review registry must match all known descriptive choices")
    return records


def pending_cartridge_review(category: str, requested_description: str, *, position: int | None = None) -> PendingCartridgeReview:
    """Review one descriptive option; housing position never implies approval."""
    if position is not None and (type(position) is not int or position not in (1, 2, 3)):
        raise ValueError("Unknown Pureline physical housing position")
    try:
        return load_pending_pureline_reviews()[(category, requested_description)]
    except KeyError as exc:
        raise ValueError("Unknown Pureline review option") from exc

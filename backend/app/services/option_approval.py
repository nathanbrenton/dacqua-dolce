"""PT54-C: fail-closed review status for currently unapproved hardware requests.

This is deliberately NOT a product catalog, compatibility certification, BOM,
price list, or purchasing authorization. Supplier records have not yet been
approved for any current fitting/valve pairing or Pureline cartridge choice.

Promotion of an option to a priced/orderable part requires a separate reviewed
commercial-data implementation and evidence; do not add guessed approvals here.
"""

from dataclasses import dataclass
from typing import Literal

from app.schemas.product_configuration import CARTRIDGE_CHOICES, FITTING_CHOICES
from app.services.pureline_commercial_review import pending_cartridge_review


@dataclass(frozen=True, slots=True)
class OptionApprovalReview:
    """A structured negative authorization; status is not a compatibility verdict."""

    approval_status: Literal["unverified"] = "unverified"
    compatibility_confirmed: bool = False
    sales_price_authorized: bool = False
    approved_supplier_model: None = None
    evidence_reference: None = None
    staff_review_required: bool = True


def review_fitting(valve: str, order_no: str) -> OptionApprovalReview:
    """Accept known inquiry references only; fail closed for all valve pairings."""

    if valve not in {"clack", "performance"}:
        raise ValueError("Unknown valve for fitting review")
    if order_no not in FITTING_CHOICES:
        raise ValueError("Unknown reference fitting for review")
    return OptionApprovalReview()


def review_pureline_cartridge(category: str, cartridge: str | None) -> OptionApprovalReview:
    """Reference-only cartridge descriptions; no approved fitment or sales pricing."""

    if category == "other":
        if cartridge is not None:
            raise ValueError("Other cartridge inquiries must not claim a catalog model")
    elif category not in CARTRIDGE_CHOICES:
        raise ValueError("Unknown Pureline cartridge category")
    elif cartridge is not None:
        # Validate against the dedicated pending commercial review register.
        # This still cannot authorize fitment, sales, or pricing.
        pending_cartridge_review(category, cartridge)
    return OptionApprovalReview()

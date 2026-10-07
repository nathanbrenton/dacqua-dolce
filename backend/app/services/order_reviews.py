from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.commerce import Order
from app.services.audit import record_audit_event


class OrderReviewError(ValueError):
    """Raised when an order review or hold transition is invalid."""


def _clean_required(value: str | None, *, label: str, max_length: int) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise OrderReviewError(f"{label} is required.")
    if len(cleaned) > max_length:
        raise OrderReviewError(f"{label} is too long.")
    return cleaned


def order_review_completed(order: Order) -> bool:
    return (
        getattr(order, "reviewed_at", None) is not None
        and getattr(order, "reviewed_by_user_id", None) is not None
    )


def order_review_on_hold(order: Order) -> bool:
    return bool(getattr(order, "review_on_hold", False))


def update_order_review(
    db: Session,
    *,
    order: Order,
    actor_user_id: uuid.UUID,
    customer_contact_reviewed: bool,
    supplier_availability_verified: bool,
    whole_order_reviewed: bool,
    customer_contact_required: bool,
    customer_contact_completed: bool,
    complete: bool,
    now: datetime | None = None,
) -> Order:
    """Save the guided checklist and optionally complete formal Order Reviewed.

    Completed review evidence is immutable. A later fulfillment problem is handled
    through the independent order-hold workflow rather than rewriting who reviewed
    the order or when the review was completed.
    """

    if order_review_completed(order):
        raise OrderReviewError(
            "Order Reviewed is already complete and its review evidence is immutable."
        )

    order.review_customer_contact_reviewed = customer_contact_reviewed
    order.review_supplier_availability_verified = supplier_availability_verified
    order.review_whole_order_reviewed = whole_order_reviewed
    order.review_customer_contact_required = customer_contact_required
    order.review_customer_contact_completed = customer_contact_completed

    if not complete:
        record_audit_event(
            db,
            action="order.review_checklist_updated",
            entity_type="order",
            entity_id=str(order.id),
            actor_user_id=actor_user_id,
            metadata={
                "customer_contact_reviewed": customer_contact_reviewed,
                "supplier_availability_verified": supplier_availability_verified,
                "whole_order_reviewed": whole_order_reviewed,
                "customer_contact_required": customer_contact_required,
                "customer_contact_completed": customer_contact_completed,
            },
        )
        db.flush()
        return order

    if order_review_on_hold(order):
        raise OrderReviewError(
            "Order Reviewed cannot be completed while the order is on hold."
        )

    missing: list[str] = []
    if not customer_contact_reviewed:
        missing.append("customer/contact review")
    if not supplier_availability_verified:
        missing.append("supplier availability verification")
    if not whole_order_reviewed:
        missing.append("whole-order review")
    if customer_contact_required and not customer_contact_completed:
        missing.append("required customer contact")

    if missing:
        raise OrderReviewError(
            "Complete the review checklist before marking Order Reviewed: "
            + ", ".join(missing)
            + "."
        )

    effective_now = now or datetime.now(UTC)
    order.reviewed_by_user_id = actor_user_id
    order.reviewed_at = effective_now

    record_audit_event(
        db,
        action="order.review_completed",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=actor_user_id,
        metadata={
            "customer_contact_required": customer_contact_required,
            "customer_contact_completed": customer_contact_completed,
            "reviewed_at": effective_now.isoformat(),
        },
    )
    db.flush()
    return order


def place_order_on_hold(
    db: Session,
    *,
    order: Order,
    actor_user_id: uuid.UUID,
    reason: str,
    proposed_alternative: str,
    now: datetime | None = None,
) -> Order:
    """Place an order on hold pending customer response.

    The workflow records an explicitly proposed alternative but never changes an
    order item or substitutes a product automatically.
    """

    if order_review_completed(order):
        raise OrderReviewError(
            "A completed Order Reviewed record cannot be placed into the pre-review hold workflow."
        )
    if order_review_on_hold(order):
        raise OrderReviewError("This order is already on hold.")

    reason_clean = _clean_required(
        reason,
        label="Hold reason",
        max_length=4000,
    )
    alternative_clean = _clean_required(
        proposed_alternative,
        label="Proposed alternative",
        max_length=4000,
    )
    effective_now = now or datetime.now(UTC)

    order.review_on_hold = True
    order.review_hold_reason = reason_clean
    order.review_proposed_alternative = alternative_clean
    order.review_hold_started_by_user_id = actor_user_id
    order.review_hold_started_at = effective_now
    order.review_hold_released_by_user_id = None
    order.review_hold_released_at = None
    order.review_customer_response_note = None

    # A cannot-fulfill hold always requires customer contact before resolution.
    order.review_customer_contact_required = True
    order.review_customer_contact_completed = False

    record_audit_event(
        db,
        action="order.review_hold_started",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=actor_user_id,
        metadata={
            "reason": reason_clean,
            "proposed_alternative": alternative_clean,
            "hold_started_at": effective_now.isoformat(),
            "automatic_substitution": False,
        },
    )
    db.flush()
    return order


def release_order_hold(
    db: Session,
    *,
    order: Order,
    actor_user_id: uuid.UUID,
    customer_response_note: str,
    now: datetime | None = None,
) -> Order:
    """Release an active order hold after customer response is recorded."""

    if not order_review_on_hold(order):
        raise OrderReviewError("This order is not currently on hold.")

    response_clean = _clean_required(
        customer_response_note,
        label="Customer response note",
        max_length=4000,
    )
    effective_now = now or datetime.now(UTC)

    order.review_on_hold = False
    order.review_customer_contact_completed = True
    order.review_customer_response_note = response_clean
    order.review_hold_released_by_user_id = actor_user_id
    order.review_hold_released_at = effective_now

    record_audit_event(
        db,
        action="order.review_hold_released",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=actor_user_id,
        metadata={
            "customer_response_note": response_clean,
            "hold_released_at": effective_now.isoformat(),
        },
    )
    db.flush()
    return order

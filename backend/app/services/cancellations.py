from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.commerce import (
    FulfillmentStatus,
    Order,
    OrderCancellationRequest,
    OrderStatus,
)
from app.services.audit import record_audit_event

UNRESTRICTED = "unrestricted"
MANUAL_REVIEW = "manual_review"

REQUESTED = "requested"
APPROVED = "approved"
DECLINED = "declined"
COMPLETED = "completed"


class CancellationError(ValueError):
    pass


def cancellation_mode_for_order(order: Order) -> str:
    if (
        order.supplier_ordered_at is None
        and order.fulfillment_status == FulfillmentStatus.not_started
    ):
        return UNRESTRICTED
    return MANUAL_REVIEW


def get_order_cancellation_request(
    db: Session,
    *,
    order_id: uuid.UUID,
) -> OrderCancellationRequest | None:
    return db.scalar(
        select(OrderCancellationRequest).where(
            OrderCancellationRequest.order_id == order_id,
        )
    )


def _clean_optional_text(
    value: str | None,
    *,
    max_length: int,
    label: str,
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise CancellationError(f"{label} is too long.")
    return cleaned


def request_order_cancellation(
    db: Session,
    *,
    order: Order,
    actor_user_id: uuid.UUID,
    reason: str | None = None,
    now: datetime | None = None,
) -> OrderCancellationRequest:
    if order.status in {
        OrderStatus.cancelled,
        OrderStatus.refunded,
    }:
        raise CancellationError(
            "This order is already in a terminal cancellation/refund state."
        )

    existing = get_order_cancellation_request(
        db,
        order_id=order.id,
    )
    if existing is not None:
        raise CancellationError(
            "A cancellation request already exists for this order."
        )

    mode = cancellation_mode_for_order(order)
    effective_now = now or datetime.now(UTC)
    initial_status = APPROVED if mode == UNRESTRICTED else REQUESTED

    row = OrderCancellationRequest(
        order_id=order.id,
        requested_by_user_id=actor_user_id,
        eligibility_mode=mode,
        status=initial_status,
        reason=_clean_optional_text(
            reason,
            max_length=2000,
            label="Cancellation reason",
        ),
        supplier_ordered_at_snapshot=order.supplier_ordered_at,
        reviewed_at=(
            effective_now
            if initial_status == APPROVED
            else None
        ),
    )
    db.add(row)
    db.flush()

    record_audit_event(
        db,
        action="order.cancellation_requested",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=actor_user_id,
        metadata={
            "eligibility_mode": mode,
            "status": initial_status,
            "supplier_confirmed": mode == MANUAL_REVIEW,
        },
    )
    db.flush()
    return row


def review_order_cancellation(
    db: Session,
    *,
    cancellation: OrderCancellationRequest,
    actor_user_id: uuid.UUID,
    action: str,
    note: str | None = None,
    now: datetime | None = None,
) -> OrderCancellationRequest:
    if action not in {
        "approve",
        "decline",
        "complete",
    }:
        raise CancellationError("Unsupported cancellation action.")

    effective_now = now or datetime.now(UTC)
    cleaned_note = _clean_optional_text(
        note,
        max_length=4000,
        label="Cancellation review note",
    )
    previous_status = cancellation.status

    if action in {"approve", "decline"}:
        if cancellation.status != REQUESTED:
            raise CancellationError(
                "Only a cancellation awaiting review can be approved or declined."
            )

        cancellation.status = (
            APPROVED
            if action == "approve"
            else DECLINED
        )
        cancellation.reviewed_by_user_id = actor_user_id
        cancellation.reviewed_at = effective_now
        cancellation.review_note = cleaned_note
        audit_action = "order.cancellation_reviewed"

    else:
        if cancellation.status != APPROVED:
            raise CancellationError(
                "Only an approved cancellation can be marked complete."
            )

        cancellation.status = COMPLETED
        cancellation.completed_by_user_id = actor_user_id
        cancellation.completed_at = effective_now
        if cleaned_note is not None and cancellation.review_note is None:
            cancellation.review_note = cleaned_note
        audit_action = "order.cancellation_completed"

    record_audit_event(
        db,
        action=audit_action,
        entity_type="order",
        entity_id=str(cancellation.order_id),
        actor_user_id=actor_user_id,
        metadata={
            "eligibility_mode": cancellation.eligibility_mode,
            "previous_status": previous_status,
            "new_status": cancellation.status,
            "payment_action_automated": False,
        },
    )
    db.flush()
    return cancellation

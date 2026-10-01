import uuid
from datetime import UTC, datetime

import pytest

from app.models.audit import AuditEvent
from app.models.commerce import (
    FulfillmentStatus,
    Order,
    OrderCancellationRequest,
    OrderStatus,
)
from app.services.cancellations import (
    CancellationError,
    cancellation_mode_for_order,
    request_order_cancellation,
    review_order_cancellation,
)


class CancellationDatabase:
    def __init__(
        self,
        cancellation: OrderCancellationRequest | None = None,
    ) -> None:
        self.cancellation = cancellation
        self.added: list[object] = []

    def scalar(self, statement: object):
        query = str(statement)
        if "FROM order_cancellation_requests" in query:
            return self.cancellation
        raise AssertionError(query)

    def add(self, value: object) -> None:
        self.added.append(value)
        if isinstance(value, OrderCancellationRequest):
            self.cancellation = value

    def flush(self) -> None:
        for value in self.added:
            if getattr(value, "id", None) is None and hasattr(value, "id"):
                value.id = uuid.uuid4()


def make_order(
    *,
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.not_started,
    supplier_ordered_at: datetime | None = None,
    status: OrderStatus = OrderStatus.paid,
) -> Order:
    return Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=status,
        fulfillment_status=fulfillment_status,
        supplier_ordered_at=supplier_ordered_at,
        subtotal_amount_minor=250000,
        charges_amount_minor=0,
        total_amount_minor=250000,
        currency="USD",
    )


def test_pre_supplier_cancellation_is_automatically_approved() -> None:
    db = CancellationDatabase()
    order = make_order()
    now = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)

    cancellation = request_order_cancellation(
        db,  # type: ignore[arg-type]
        order=order,
        actor_user_id=order.user_id,
        reason="Changed plans",
        now=now,
    )

    assert cancellation.eligibility_mode == "unrestricted"
    assert cancellation.status == "approved"
    assert cancellation.reason == "Changed plans"
    assert cancellation.reviewed_at == now
    assert cancellation.supplier_ordered_at_snapshot is None
    assert any(isinstance(value, AuditEvent) for value in db.added)


def test_post_supplier_cancellation_enters_manual_review() -> None:
    supplier_ordered_at = datetime(2026, 10, 1, 18, 0, tzinfo=UTC)
    db = CancellationDatabase()
    order = make_order(
        fulfillment_status=FulfillmentStatus.supplier_ordered,
        supplier_ordered_at=supplier_ordered_at,
    )

    cancellation = request_order_cancellation(
        db,  # type: ignore[arg-type]
        order=order,
        actor_user_id=order.user_id,
    )

    assert cancellation_mode_for_order(order) == "manual_review"
    assert cancellation.eligibility_mode == "manual_review"
    assert cancellation.status == "requested"
    assert cancellation.reviewed_at is None
    assert cancellation.supplier_ordered_at_snapshot == supplier_ordered_at


def test_duplicate_cancellation_request_is_rejected() -> None:
    order = make_order()
    existing = OrderCancellationRequest(
        id=uuid.uuid4(),
        order_id=order.id,
        requested_by_user_id=order.user_id,
        eligibility_mode="unrestricted",
        status="approved",
    )
    db = CancellationDatabase(existing)

    with pytest.raises(CancellationError, match="already exists"):
        request_order_cancellation(
            db,  # type: ignore[arg-type]
            order=order,
            actor_user_id=order.user_id,
        )


def test_terminal_order_cannot_start_cancellation() -> None:
    db = CancellationDatabase()
    order = make_order(status=OrderStatus.refunded)

    with pytest.raises(CancellationError, match="terminal"):
        request_order_cancellation(
            db,  # type: ignore[arg-type]
            order=order,
            actor_user_id=order.user_id,
        )


def test_manual_review_can_be_approved_then_completed() -> None:
    order_id = uuid.uuid4()
    cancellation = OrderCancellationRequest(
        id=uuid.uuid4(),
        order_id=order_id,
        requested_by_user_id=uuid.uuid4(),
        eligibility_mode="manual_review",
        status="requested",
    )
    db = CancellationDatabase(cancellation)
    reviewer = uuid.uuid4()
    reviewed_at = datetime(2026, 10, 1, 21, 0, tzinfo=UTC)

    review_order_cancellation(
        db,  # type: ignore[arg-type]
        cancellation=cancellation,
        actor_user_id=reviewer,
        action="approve",
        note="Supplier confirmed cancellation is available.",
        now=reviewed_at,
    )

    assert cancellation.status == "approved"
    assert cancellation.reviewed_by_user_id == reviewer
    assert cancellation.reviewed_at == reviewed_at
    assert cancellation.review_note == (
        "Supplier confirmed cancellation is available."
    )

    completed_by = uuid.uuid4()
    completed_at = datetime(2026, 10, 1, 22, 0, tzinfo=UTC)
    review_order_cancellation(
        db,  # type: ignore[arg-type]
        cancellation=cancellation,
        actor_user_id=completed_by,
        action="complete",
        now=completed_at,
    )

    assert cancellation.status == "completed"
    assert cancellation.completed_by_user_id == completed_by
    assert cancellation.completed_at == completed_at


def test_only_pending_manual_review_can_be_declined() -> None:
    cancellation = OrderCancellationRequest(
        id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        requested_by_user_id=uuid.uuid4(),
        eligibility_mode="unrestricted",
        status="approved",
    )
    db = CancellationDatabase(cancellation)

    with pytest.raises(CancellationError, match="awaiting review"):
        review_order_cancellation(
            db,  # type: ignore[arg-type]
            cancellation=cancellation,
            actor_user_id=uuid.uuid4(),
            action="decline",
        )

import uuid
from datetime import UTC, datetime
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.commerce import (
    FulfillmentStatus,
    Order,
    OrderShipment,
    OrderStatus,
)
from app.services.audit import record_audit_event
from app.services.cancellations import get_order_cancellation_request
from app.services.order_reviews import order_review_on_hold

ALLOWED_FULFILLMENT_TRANSITIONS: dict[
    FulfillmentStatus,
    frozenset[FulfillmentStatus],
] = {
    FulfillmentStatus.not_started: frozenset(
        {FulfillmentStatus.supplier_ordered}
    ),
    FulfillmentStatus.supplier_ordered: frozenset(
        {FulfillmentStatus.received_ready}
    ),
    FulfillmentStatus.received_ready: frozenset(
        {FulfillmentStatus.shipped}
    ),
    FulfillmentStatus.shipped: frozenset(
        {FulfillmentStatus.delivered}
    ),
    FulfillmentStatus.delivered: frozenset(),
}


class FulfillmentError(ValueError):
    pass


def _clean_optional(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise FulfillmentError("Fulfillment value is too long.")
    return cleaned


def _clean_required(value: str | None, *, label: str, max_length: int) -> str:
    cleaned = _clean_optional(value, max_length=max_length)
    if cleaned is None:
        raise FulfillmentError(f"{label} is required.")
    return cleaned


def _clean_tracking_url(value: str | None) -> str | None:
    cleaned = _clean_optional(value, max_length=2048)
    if cleaned is None:
        return None

    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.netloc:
        raise FulfillmentError("Tracking URL must be an HTTPS URL.")

    return cleaned


def get_order_shipment(
    db: Session,
    *,
    order_id: uuid.UUID,
) -> OrderShipment | None:
    return db.scalar(
        select(OrderShipment).where(
            OrderShipment.order_id == order_id,
        )
    )


def transition_order_fulfillment(
    db: Session,
    *,
    order: Order,
    actor_user_id: uuid.UUID,
    new_status: FulfillmentStatus,
    supplier_order_reference: str | None = None,
    carrier: str | None = None,
    tracking_number: str | None = None,
    tracking_url: str | None = None,
    now: datetime | None = None,
) -> OrderShipment | None:
    previous = order.fulfillment_status

    if new_status == previous:
        return get_order_shipment(db, order_id=order.id)

    if order_review_on_hold(order):
        raise FulfillmentError(
            "Fulfillment cannot advance while the order is on hold pending customer response."
        )

    if order.status != OrderStatus.paid:
        raise FulfillmentError(
            "Only a paid order can advance through fulfillment."
        )

    if new_status not in ALLOWED_FULFILLMENT_TRANSITIONS[previous]:
        raise FulfillmentError(
            "Cannot transition fulfillment from "
            f"{previous.value} to {new_status.value}."
        )

    effective_now = now or datetime.now(UTC)
    shipment = get_order_shipment(db, order_id=order.id)

    if new_status == FulfillmentStatus.supplier_ordered:
        cancellation = get_order_cancellation_request(
            db,
            order_id=order.id,
        )
        if (
            cancellation is not None
            and cancellation.status != "declined"
        ):
            raise FulfillmentError(
                "Supplier ordering is blocked while a cancellation request is active."
            )
        order.supplier_order_reference = _clean_optional(
            supplier_order_reference,
            max_length=160,
        )
        order.supplier_ordered_at = effective_now

    elif new_status == FulfillmentStatus.received_ready:
        order.received_ready_at = effective_now

    elif new_status == FulfillmentStatus.shipped:
        carrier_clean = _clean_required(
            carrier,
            label="Carrier",
            max_length=100,
        )
        tracking_number_clean = _clean_required(
            tracking_number,
            label="Tracking number",
            max_length=200,
        )
        tracking_url_clean = _clean_tracking_url(tracking_url)

        if shipment is not None:
            raise FulfillmentError(
                "A shipment is already recorded for this order."
            )

        shipment = OrderShipment(
            order_id=order.id,
            carrier=carrier_clean,
            tracking_number=tracking_number_clean,
            tracking_url=tracking_url_clean,
            created_by_user_id=actor_user_id,
        )
        db.add(shipment)
        order.shipped_at = effective_now

        record_audit_event(
            db,
            action="order.shipment_recorded",
            entity_type="order",
            entity_id=str(order.id),
            actor_user_id=actor_user_id,
            metadata={
                "carrier": carrier_clean,
                "tracking_number": tracking_number_clean,
            },
        )

    elif new_status == FulfillmentStatus.delivered:
        if shipment is None:
            raise FulfillmentError(
                "A shipment must exist before an order can be delivered."
            )
        order.delivered_at = effective_now

    order.fulfillment_status = new_status
    order.fulfillment_updated_at = effective_now

    metadata: dict[str, object] = {
        "previous_status": previous.value,
        "new_status": new_status.value,
    }
    if new_status == FulfillmentStatus.supplier_ordered:
        metadata.update(
            {
                "customer_status": "supplier_confirmed",
                "cancellation_boundary_closed": True,
            }
        )

    record_audit_event(
        db,
        action="order.fulfillment_status_changed",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=actor_user_id,
        metadata=metadata,
    )

    db.flush()
    return shipment

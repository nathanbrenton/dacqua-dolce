from sqlalchemy.orm import Session

from app.models.commerce import (
    Order,
    OrderStatus,
)
from app.services.audit import (
    record_audit_event,
)

ALLOWED_ORDER_TRANSITIONS: dict[
    OrderStatus,
    frozenset[OrderStatus],
] = {
    OrderStatus.draft: frozenset(
        {
            OrderStatus.awaiting_payment,
            OrderStatus.cancelled,
        }
    ),
    OrderStatus.awaiting_payment: frozenset(
        {
            OrderStatus.paid,
            OrderStatus.cancelled,
        }
    ),
    OrderStatus.paid: frozenset(
        {
            OrderStatus.processing,
            OrderStatus.refunded,
        }
    ),
    OrderStatus.processing: frozenset(
        {
            OrderStatus.shipped,
            OrderStatus.cancelled,
            OrderStatus.refunded,
        }
    ),
    OrderStatus.shipped: frozenset(
        {
            OrderStatus.delivered,
            OrderStatus.refunded,
        }
    ),
    OrderStatus.delivered: frozenset(
        {
            OrderStatus.refunded,
        }
    ),
    OrderStatus.cancelled: frozenset(),
    OrderStatus.refunded: frozenset(),
}


class InvalidOrderTransition(ValueError):
    pass


def transition_order_status(
    db: Session,
    *,
    order: Order,
    new_status: OrderStatus,
) -> None:
    previous = order.status

    if new_status == previous:
        return

    if new_status not in ALLOWED_ORDER_TRANSITIONS[previous]:
        raise InvalidOrderTransition(
            f"Cannot transition order from {previous.value} to {new_status.value}."
        )

    order.status = new_status

    record_audit_event(
        db,
        action="order.status_changed",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=order.user_id,
        metadata={
            "previous_status": previous.value,
            "new_status": new_status.value,
        },
    )

    db.flush()

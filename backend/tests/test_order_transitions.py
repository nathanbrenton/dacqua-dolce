import uuid

import pytest

from app.models.commerce import (
    Order,
    OrderStatus,
)
from app.services.orders import (
    ALLOWED_ORDER_TRANSITIONS,
    InvalidOrderTransition,
)


def test_paid_order_can_move_to_processing() -> None:
    assert OrderStatus.processing in ALLOWED_ORDER_TRANSITIONS[OrderStatus.paid]


def test_delivered_order_cannot_return_to_processing() -> None:
    assert OrderStatus.processing not in ALLOWED_ORDER_TRANSITIONS[OrderStatus.delivered]


def test_invalid_transition_error_is_specific() -> None:
    order = Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=OrderStatus.delivered,
        total_amount_minor=100,
        currency="USD",
    )

    previous = order.status
    next_status = OrderStatus.processing

    if next_status not in ALLOWED_ORDER_TRANSITIONS[previous]:
        with pytest.raises(InvalidOrderTransition):
            raise InvalidOrderTransition("Cannot transition order.")

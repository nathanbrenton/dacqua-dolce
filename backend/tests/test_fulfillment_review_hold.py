from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.models.commerce import FulfillmentStatus, OrderStatus
from app.services.fulfillment import FulfillmentError, transition_order_fulfillment


def test_active_review_hold_blocks_fulfillment_advance() -> None:
    order = SimpleNamespace(
        id=uuid.uuid4(),
        status=OrderStatus.paid,
        fulfillment_status=FulfillmentStatus.not_started,
        review_on_hold=True,
    )

    with pytest.raises(FulfillmentError, match="on hold pending customer response"):
        transition_order_fulfillment(
            SimpleNamespace(),  # type: ignore[arg-type]
            order=order,  # type: ignore[arg-type]
            actor_user_id=uuid.uuid4(),
            new_status=FulfillmentStatus.supplier_ordered,
        )

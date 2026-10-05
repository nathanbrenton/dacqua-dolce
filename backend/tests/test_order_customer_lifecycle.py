import uuid

import pytest

from app.models.commerce import FulfillmentStatus, Order, OrderStatus
from app.services.order_lifecycle import (
    CustomerOrderStage,
    customer_order_stage,
    supplier_confirmation_recorded,
)


def make_order(
    *,
    status: OrderStatus,
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.not_started,
) -> Order:
    return Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=status,
        fulfillment_status=fulfillment_status,
        subtotal_amount_minor=100,
        charges_amount_minor=0,
        total_amount_minor=100,
        currency="USD",
    )


@pytest.mark.parametrize(
    ("status", "fulfillment", "expected"),
    [
        (
            OrderStatus.awaiting_payment,
            FulfillmentStatus.not_started,
            CustomerOrderStage.received,
        ),
        (
            OrderStatus.paid,
            FulfillmentStatus.not_started,
            CustomerOrderStage.processing,
        ),
        (
            OrderStatus.paid,
            FulfillmentStatus.supplier_ordered,
            CustomerOrderStage.supplier_confirmed,
        ),
        (
            OrderStatus.paid,
            FulfillmentStatus.received_ready,
            CustomerOrderStage.awaiting_shipment,
        ),
        (
            OrderStatus.paid,
            FulfillmentStatus.shipped,
            CustomerOrderStage.shipped,
        ),
        (
            OrderStatus.paid,
            FulfillmentStatus.delivered,
            CustomerOrderStage.completed,
        ),
    ],
)
def test_customer_order_stage_maps_internal_states(
    status: OrderStatus,
    fulfillment: FulfillmentStatus,
    expected: CustomerOrderStage,
) -> None:
    order = make_order(status=status, fulfillment_status=fulfillment)
    assert customer_order_stage(order) == expected


def test_terminal_order_statuses_override_fulfillment() -> None:
    cancelled = make_order(
        status=OrderStatus.cancelled,
        fulfillment_status=FulfillmentStatus.not_started,
    )
    refunded = make_order(
        status=OrderStatus.refunded,
        fulfillment_status=FulfillmentStatus.shipped,
    )

    assert customer_order_stage(cancelled) == CustomerOrderStage.cancelled
    assert customer_order_stage(refunded) == CustomerOrderStage.refunded


def test_supplier_confirmation_boundary_is_durable() -> None:
    before = make_order(
        status=OrderStatus.paid,
        fulfillment_status=FulfillmentStatus.not_started,
    )
    after = make_order(
        status=OrderStatus.paid,
        fulfillment_status=FulfillmentStatus.supplier_ordered,
    )

    assert supplier_confirmation_recorded(before) is False
    assert supplier_confirmation_recorded(after) is True

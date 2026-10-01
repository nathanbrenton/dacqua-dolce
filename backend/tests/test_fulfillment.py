import uuid
from datetime import UTC, datetime

import pytest

from app.models.audit import AuditEvent
from app.models.commerce import (
    FulfillmentStatus,
    Order,
    OrderCancellationRequest,
    OrderShipment,
    OrderStatus,
)
from app.services.fulfillment import (
    FulfillmentError,
    transition_order_fulfillment,
)


class FulfillmentDatabase:
    def __init__(
        self,
        cancellation: OrderCancellationRequest | None = None,
    ) -> None:
        self.shipment: OrderShipment | None = None
        self.cancellation = cancellation
        self.added: list[object] = []

    def scalar(self, statement: object):
        query = str(statement)
        if "FROM order_shipments" in query:
            return self.shipment
        if "FROM order_cancellation_requests" in query:
            return self.cancellation
        raise AssertionError(query)

    def add(self, value: object) -> None:
        self.added.append(value)
        if isinstance(value, OrderShipment):
            self.shipment = value

    def flush(self) -> None:
        for value in self.added:
            if getattr(value, "id", None) is None and hasattr(value, "id"):
                value.id = uuid.uuid4()


def make_order(
    *,
    payment_status: OrderStatus = OrderStatus.paid,
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.not_started,
) -> Order:
    return Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status=payment_status,
        fulfillment_status=fulfillment_status,
        subtotal_amount_minor=250000,
        charges_amount_minor=0,
        total_amount_minor=250000,
        currency="USD",
    )


def test_paid_order_advances_to_supplier_ordered() -> None:
    db = FulfillmentDatabase()
    order = make_order()
    actor_id = uuid.uuid4()
    now = datetime(2026, 9, 29, 20, 0, tzinfo=UTC)

    shipment = transition_order_fulfillment(
        db,  # type: ignore[arg-type]
        order=order,
        actor_user_id=actor_id,
        new_status=FulfillmentStatus.supplier_ordered,
        supplier_order_reference="  PO-12345  ",
        now=now,
    )

    assert shipment is None
    assert order.fulfillment_status == FulfillmentStatus.supplier_ordered
    assert order.supplier_order_reference == "PO-12345"
    assert order.supplier_ordered_at == now
    assert order.fulfillment_updated_at == now
    assert any(isinstance(value, AuditEvent) for value in db.added)


def test_active_cancellation_blocks_supplier_ordering() -> None:
    order = make_order()
    cancellation = OrderCancellationRequest(
        id=uuid.uuid4(),
        order_id=order.id,
        requested_by_user_id=order.user_id,
        eligibility_mode="unrestricted",
        status="approved",
    )
    db = FulfillmentDatabase(cancellation)

    with pytest.raises(FulfillmentError, match="cancellation"):
        transition_order_fulfillment(
            db,  # type: ignore[arg-type]
            order=order,
            actor_user_id=uuid.uuid4(),
            new_status=FulfillmentStatus.supplier_ordered,
        )

    assert order.fulfillment_status == FulfillmentStatus.not_started


def test_unpaid_order_cannot_advance_fulfillment() -> None:
    db = FulfillmentDatabase()
    order = make_order(payment_status=OrderStatus.awaiting_payment)

    with pytest.raises(FulfillmentError, match="paid"):
        transition_order_fulfillment(
            db,  # type: ignore[arg-type]
            order=order,
            actor_user_id=uuid.uuid4(),
            new_status=FulfillmentStatus.supplier_ordered,
        )

    assert order.fulfillment_status == FulfillmentStatus.not_started
    assert db.added == []


def test_fulfillment_cannot_skip_received_ready() -> None:
    db = FulfillmentDatabase()
    order = make_order(
        fulfillment_status=FulfillmentStatus.supplier_ordered,
    )

    with pytest.raises(FulfillmentError, match="Cannot transition"):
        transition_order_fulfillment(
            db,  # type: ignore[arg-type]
            order=order,
            actor_user_id=uuid.uuid4(),
            new_status=FulfillmentStatus.shipped,
            carrier="UPS",
            tracking_number="1Z999",
        )


def test_shipping_requires_carrier_and_tracking_number() -> None:
    db = FulfillmentDatabase()
    order = make_order(
        fulfillment_status=FulfillmentStatus.received_ready,
    )

    with pytest.raises(FulfillmentError, match="Carrier"):
        transition_order_fulfillment(
            db,  # type: ignore[arg-type]
            order=order,
            actor_user_id=uuid.uuid4(),
            new_status=FulfillmentStatus.shipped,
            tracking_number="1Z999",
        )

    assert db.shipment is None


def test_shipping_records_safe_tracking_metadata() -> None:
    db = FulfillmentDatabase()
    order = make_order(
        fulfillment_status=FulfillmentStatus.received_ready,
    )
    actor_id = uuid.uuid4()
    now = datetime(2026, 9, 29, 21, 0, tzinfo=UTC)

    shipment = transition_order_fulfillment(
        db,  # type: ignore[arg-type]
        order=order,
        actor_user_id=actor_id,
        new_status=FulfillmentStatus.shipped,
        carrier="UPS",
        tracking_number="1Z999",
        tracking_url="https://www.ups.com/track?loc=en_US",
        now=now,
    )

    assert shipment is not None
    assert shipment.carrier == "UPS"
    assert shipment.tracking_number == "1Z999"
    assert shipment.created_by_user_id == actor_id
    assert order.fulfillment_status == FulfillmentStatus.shipped
    assert order.shipped_at == now


def test_tracking_url_must_be_https() -> None:
    db = FulfillmentDatabase()
    order = make_order(
        fulfillment_status=FulfillmentStatus.received_ready,
    )

    with pytest.raises(FulfillmentError, match="HTTPS"):
        transition_order_fulfillment(
            db,  # type: ignore[arg-type]
            order=order,
            actor_user_id=uuid.uuid4(),
            new_status=FulfillmentStatus.shipped,
            carrier="Freight carrier",
            tracking_number="FREIGHT-1",
            tracking_url="http://example.com/track/FREIGHT-1",
        )


def test_shipped_order_can_be_marked_delivered() -> None:
    db = FulfillmentDatabase()
    order = make_order(
        fulfillment_status=FulfillmentStatus.shipped,
    )
    db.shipment = OrderShipment(
        id=uuid.uuid4(),
        order_id=order.id,
        carrier="UPS",
        tracking_number="1Z999",
        created_by_user_id=uuid.uuid4(),
    )
    now = datetime(2026, 9, 30, 18, 0, tzinfo=UTC)

    shipment = transition_order_fulfillment(
        db,  # type: ignore[arg-type]
        order=order,
        actor_user_id=uuid.uuid4(),
        new_status=FulfillmentStatus.delivered,
        now=now,
    )

    assert shipment is db.shipment
    assert order.fulfillment_status == FulfillmentStatus.delivered
    assert order.delivered_at == now

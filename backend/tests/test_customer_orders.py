import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.api import orders
from app.models.commerce import FulfillmentStatus, OrderStatus


class ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class CustomerOrdersDatabase:
    def __init__(
        self,
        *,
        order: object,
        item: object,
        shipment: object,
    ) -> None:
        self.order = order
        self.item = item
        self.shipment = shipment

    def scalars(self, statement: object) -> ScalarResult:
        query = str(statement)

        if "FROM orders" in query:
            return ScalarResult([self.order])
        if "FROM order_items" in query:
            return ScalarResult([self.item])
        if "FROM order_shipments" in query:
            return ScalarResult([self.shipment])

        raise AssertionError(query)


def test_customer_order_exposes_fulfillment_and_tracking_without_supplier_reference() -> None:
    customer_id = uuid.uuid4()
    order_id = uuid.uuid4()
    shipped_at = datetime.now(UTC)

    order = SimpleNamespace(
        id=order_id,
        user_id=customer_id,
        formal_quote_id=uuid.uuid4(),
        status=OrderStatus.paid,
        fulfillment_status=FulfillmentStatus.shipped,
        supplier_order_reference="INTERNAL-PO-123",
        shipped_at=shipped_at,
        delivered_at=None,
        total_amount_minor=249900,
        currency="USD",
        created_at=datetime.now(UTC),
    )
    item = SimpleNamespace(
        sku_snapshot="DD5RO",
        name_snapshot="Origin",
        quantity=1,
        unit_amount_minor=249900,
        line_total_minor=249900,
        currency="USD",
        estimated_lead_time_snapshot="2–3 weeks",
        created_at=datetime.now(UTC),
    )
    shipment = SimpleNamespace(
        carrier="UPS",
        tracking_number="1Z999",
        tracking_url="https://www.ups.com/track",
        created_at=shipped_at,
    )

    result = orders.list_orders(
        CustomerOrdersDatabase(
            order=order,
            item=item,
            shipment=shipment,
        ),  # type: ignore[arg-type]
        SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
    )

    assert len(result) == 1
    payload = result[0].model_dump()

    assert payload["status"] == "paid"
    assert payload["fulfillment_status"] == "shipped"
    assert payload["items"][0]["estimated_lead_time"] == "2–3 weeks"
    assert payload["shipment"] == {
        "carrier": "UPS",
        "tracking_number": "1Z999",
        "tracking_url": "https://www.ups.com/track",
        "shipped_at": shipped_at.isoformat(),
        "delivered_at": None,
    }
    assert "supplier_order_reference" not in payload

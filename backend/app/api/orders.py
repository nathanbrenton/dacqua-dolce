from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
)
from app.models.commerce import (
    Order,
    OrderCharge,
    OrderItem,
    OrderShipment,
)
from app.schemas.commerce import (
    OrderItemRead,
    OrderRead,
    OrderShipmentRead,
)

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.get(
    "",
    response_model=list[OrderRead],
)
def list_orders(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OrderRead]:
    orders = db.scalars(
        select(Order).where(Order.user_id == current_user.id).order_by(Order.created_at.desc())
    ).all()

    result: list[OrderRead] = []

    for order in orders:
        items = db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.created_at)
        ).all()
        shipments = db.scalars(
            select(OrderShipment)
            .where(OrderShipment.order_id == order.id)
            .order_by(OrderShipment.created_at.desc())
        ).all()
        shipment = shipments[0] if shipments else None
        charges = db.scalars(
            select(OrderCharge)
            .where(OrderCharge.order_id == order.id)
            .order_by(OrderCharge.sort_order, OrderCharge.created_at)
        ).all()

        result.append(
            OrderRead(
                id=str(order.id),
                formal_quote_id=(
                    str(order.formal_quote_id)
                    if order.formal_quote_id is not None
                    else None
                ),
                status=order.status.value,
                fulfillment_status=order.fulfillment_status.value,
                subtotal_amount_minor=order.subtotal_amount_minor,
                charges_amount_minor=order.charges_amount_minor,
                total_amount_minor=(order.total_amount_minor),
                currency=order.currency,
                delivery_address=order.delivery_address_snapshot,
                billing_address=order.billing_address_snapshot,
                charges=[
                    {
                        "kind": charge.kind,
                        "label": charge.label,
                        "amount_minor": charge.amount_minor,
                    }
                    for charge in charges
                ],
                created_at=(order.created_at.isoformat()),
                items=[
                    OrderItemRead(
                        sku=item.sku_snapshot,
                        name=(item.name_snapshot),
                        quantity=item.quantity,
                        unit_amount_minor=(item.unit_amount_minor),
                        line_total_minor=(item.line_total_minor),
                        currency=(item.currency),
                        estimated_lead_time=(
                            item.estimated_lead_time_snapshot
                        ),
                    )
                    for item in items
                ],
                shipment=(
                    OrderShipmentRead(
                        carrier=shipment.carrier,
                        tracking_number=shipment.tracking_number,
                        tracking_url=shipment.tracking_url,
                        shipped_at=(
                            order.shipped_at.isoformat()
                            if order.shipped_at is not None
                            else None
                        ),
                        delivered_at=(
                            order.delivered_at.isoformat()
                            if order.delivered_at is not None
                            else None
                        ),
                    )
                    if shipment is not None
                    else None
                ),
            )
        )

    return result

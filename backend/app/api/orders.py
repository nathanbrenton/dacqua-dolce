import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
)
from app.models.commerce import (
    Order,
    OrderCancellationRequest,
    OrderCharge,
    OrderItem,
    OrderShipment,
)
from app.schemas.commerce import (
    OrderCancellationRead,
    OrderCancellationRequestCreate,
    OrderItemRead,
    OrderRead,
    OrderShipmentRead,
)
from app.services.cancellations import (
    CancellationError,
    cancellation_mode_for_order,
    get_order_cancellation_request,
    request_order_cancellation,
)
from app.services.order_lifecycle import customer_order_stage

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


def customer_cancellation_read(
    cancellation: OrderCancellationRequest,
) -> OrderCancellationRead:
    return OrderCancellationRead(
        id=str(cancellation.id),
        eligibility_mode=cancellation.eligibility_mode,
        status=cancellation.status,
        reason=cancellation.reason,
        requested_at=cancellation.created_at.isoformat(),
        reviewed_at=(
            cancellation.reviewed_at.isoformat()
            if cancellation.reviewed_at is not None
            else None
        ),
        completed_at=(
            cancellation.completed_at.isoformat()
            if cancellation.completed_at is not None
            else None
        ),
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
        cancellation = get_order_cancellation_request(
            db,
            order_id=order.id,
        )

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
                customer_status=customer_order_stage(order).value,
                cancellation_mode=cancellation_mode_for_order(order),
                cancellation=(
                    customer_cancellation_read(cancellation)
                    if cancellation is not None
                    else None
                ),
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


@router.post(
    "/{order_id}/cancellation",
    response_model=OrderCancellationRead,
    status_code=status.HTTP_201_CREATED,
)
def request_cancellation(
    order_id: uuid.UUID,
    payload: OrderCancellationRequestCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OrderCancellationRead:
    order = db.scalar(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    try:
        cancellation = request_order_cancellation(
            db,
            order=order,
            actor_user_id=current_user.id,
            reason=payload.reason,
        )
    except CancellationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    db.commit()
    return customer_cancellation_read(cancellation)

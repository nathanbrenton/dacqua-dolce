from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
)
from app.models.commerce import (
    Order,
    OrderItem,
)
from app.schemas.commerce import (
    OrderItemRead,
    OrderRead,
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
            select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.created_at)
        ).all()

        result.append(
            OrderRead(
                id=str(order.id),
                status=order.status.value,
                total_amount_minor=(order.total_amount_minor),
                currency=order.currency,
                created_at=(order.created_at.isoformat()),
                items=[
                    OrderItemRead(
                        sku=item.sku_snapshot,
                        name=(item.name_snapshot),
                        quantity=item.quantity,
                        unit_amount_minor=(item.unit_amount_minor),
                        line_total_minor=(item.line_total_minor),
                        currency=(item.currency),
                    )
                    for item in items
                ],
            )
        )

    return result

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.commerce import Order, OrderItem, OrderStatus
from app.models.identity import User
from app.models.quote import FormalQuote, FormalQuoteStatus
from app.services.audit import record_audit_event


def create_order_from_approved_quote(
    db: Session,
    *,
    formal_quote_id: uuid.UUID,
    customer_user: User,
) -> Order:
    """Materialize exactly one authoritative order from an approved quote.

    The quote row is locked so concurrent/retried requests cannot create two
    orders for the same approved commercial snapshot. Existing historical
    orders remain valid because ``formal_quote_id`` is nullable for them.
    """

    formal_quote = db.scalar(
        select(FormalQuote)
        .options(selectinload(FormalQuote.items))
        .where(FormalQuote.id == formal_quote_id)
        .with_for_update()
    )

    if (
        formal_quote is None
        or formal_quote.customer_user_id != customer_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found.",
        )

    existing = db.scalar(
        select(Order).where(
            Order.formal_quote_id == formal_quote.id,
        )
    )
    if existing is not None:
        if existing.user_id != customer_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )
        return existing

    if formal_quote.status != FormalQuoteStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only an approved quote can become an order.",
        )

    if formal_quote.approved_by_user_id != customer_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The approved quote is not bound to the current customer "
                "approval identity."
            ),
        )

    if not formal_quote.items:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote does not contain any orderable lines.",
        )

    subtotal = 0
    order_items: list[OrderItem] = []

    for item in formal_quote.items:
        if item.currency.upper() != formal_quote.currency.upper():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The approved quote contains inconsistent currencies.",
            )

        expected_line_total = item.unit_amount_minor * item.quantity
        if item.line_total_minor != expected_line_total:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The approved quote contains an inconsistent line total.",
            )

        subtotal += item.line_total_minor
        order_items.append(
            OrderItem(
                product_id=item.product_id,
                variant_id=item.variant_id,
                sku_snapshot=item.sku_snapshot,
                name_snapshot=item.name_snapshot,
                quantity=item.quantity,
                unit_amount_minor=item.unit_amount_minor,
                line_total_minor=item.line_total_minor,
                currency=item.currency.upper(),
            )
        )

    if subtotal != formal_quote.subtotal_amount_minor:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote subtotal does not match its line items.",
        )

    order = Order(
        user_id=customer_user.id,
        formal_quote_id=formal_quote.id,
        status=OrderStatus.awaiting_payment,
        total_amount_minor=formal_quote.subtotal_amount_minor,
        currency=formal_quote.currency.upper(),
    )
    db.add(order)
    db.flush()

    for item in order_items:
        item.order_id = order.id
        db.add(item)

    record_audit_event(
        db,
        action="order.created_from_formal_quote",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=customer_user.id,
        metadata={
            "formal_quote_id": str(formal_quote.id),
            "quote_request_id": str(formal_quote.quote_request_id),
            "revision_number": formal_quote.revision_number,
            "total_amount_minor": order.total_amount_minor,
            "currency": order.currency,
            "line_count": len(order_items),
        },
    )
    db.flush()

    return order

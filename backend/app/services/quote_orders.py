import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.sales_area import (
    SalesAreaEligibilityError,
    SalesAreaPolicy,
    require_delivery_address_in_sales_area,
)
from app.models.commerce import (
    FulfillmentStatus,
    Order,
    OrderCharge,
    OrderItem,
    OrderStatus,
)
from app.models.identity import User
from app.models.quote import (
    CommercialChargeKind,
    FormalQuote,
    FormalQuoteStatus,
    ShippingInsuranceDecision,
)
from app.services.audit import record_audit_event


def create_order_from_approved_quote(
    db: Session,
    *,
    formal_quote_id: uuid.UUID,
    customer_user: User,
    sales_area_policy: SalesAreaPolicy | None = None,
) -> Order:
    """Materialize exactly one authoritative order from an approved quote.

    The quote row is locked so concurrent/retried requests cannot create two
    orders for the same approved commercial snapshot. Existing historical
    orders remain valid because ``formal_quote_id`` is nullable for them.
    """

    formal_quote = db.scalar(
        select(FormalQuote)
        .options(
            selectinload(FormalQuote.items),
            selectinload(FormalQuote.charges),
        )
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

    insurance_amount_minor = sum(
        charge.amount_minor
        for charge in formal_quote.charges
        if charge.kind == CommercialChargeKind.shipping_insurance.value
    )
    if insurance_amount_minor > 0 and (
        formal_quote.shipping_insurance_decision
        != ShippingInsuranceDecision.accepted.value
        or formal_quote.shipping_insurance_decided_by_user_id
        != customer_user.id
        or formal_quote.shipping_insurance_decided_at is None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The approved quote does not contain complete shipping "
                "insurance acceptance evidence."
            ),
        )

    if not formal_quote.items:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote does not contain any orderable lines.",
        )

    if formal_quote.delivery_address_snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote does not contain a delivery address snapshot.",
        )
    if formal_quote.billing_address_snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote does not contain a billing address snapshot.",
        )

    try:
        require_delivery_address_in_sales_area(
            formal_quote.delivery_address_snapshot,
            policy=sales_area_policy,
        )
    except SalesAreaEligibilityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

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
                estimated_lead_time_snapshot=(
                    item.estimated_lead_time_snapshot
                ),
            )
        )

    if subtotal != formal_quote.subtotal_amount_minor:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote subtotal does not match its line items.",
        )

    charges_total = sum(charge.amount_minor for charge in formal_quote.charges)
    if charges_total != formal_quote.charges_amount_minor:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote charge total does not match its adjustments.",
        )

    expected_total = subtotal + charges_total
    if expected_total != formal_quote.total_amount_minor or expected_total <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved quote final total is inconsistent.",
        )

    order = Order(
        user_id=customer_user.id,
        formal_quote_id=formal_quote.id,
        status=OrderStatus.awaiting_payment,
        fulfillment_status=FulfillmentStatus.not_started,
        subtotal_amount_minor=formal_quote.subtotal_amount_minor,
        charges_amount_minor=formal_quote.charges_amount_minor,
        total_amount_minor=formal_quote.total_amount_minor,
        delivery_address_snapshot=dict(formal_quote.delivery_address_snapshot),
        billing_address_snapshot=dict(formal_quote.billing_address_snapshot),
        currency=formal_quote.currency.upper(),
    )
    db.add(order)
    db.flush()

    for item in order_items:
        item.order_id = order.id
        db.add(item)

    for charge in formal_quote.charges:
        db.add(
            OrderCharge(
                order_id=order.id,
                kind=charge.kind,
                label=charge.label,
                amount_minor=charge.amount_minor,
                sort_order=charge.sort_order,
            )
        )

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
            "subtotal_amount_minor": order.subtotal_amount_minor,
            "charges_amount_minor": order.charges_amount_minor,
            "total_amount_minor": order.total_amount_minor,
            "currency": order.currency,
            "line_count": len(order_items),
            "charge_count": len(formal_quote.charges),
        },
    )
    db.flush()

    return order

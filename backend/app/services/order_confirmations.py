from __future__ import annotations

import uuid
from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.email_config import EmailRuntimeSettings
from app.integrations.email import EmailMessage
from app.models.commerce import Order
from app.models.email import EmailDelivery, EmailDeliveryStatus
from app.models.identity import User
from app.services.audit import record_audit_event
from app.services.email_delivery import deliver_email
from app.services.order_lifecycle import (
    CustomerOrderStage,
    customer_order_stage,
    supplier_confirmation_recorded,
)
from app.services.order_reviews import (
    order_review_completed,
    order_review_on_hold,
)

ORDER_CONFIRMATION_CATEGORY = "order_confirmation"
ORDER_CONFIRMATION_ENTITY_TYPE = "order"


class OrderConfirmationError(RuntimeError):
    """Raised when staff cannot send an Order Confirmed message."""


def latest_order_confirmation_delivery(
    db: Session,
    *,
    order_id: uuid.UUID,
) -> EmailDelivery | None:
    return db.scalar(
        select(EmailDelivery)
        .where(
            EmailDelivery.category == ORDER_CONFIRMATION_CATEGORY,
            EmailDelivery.related_entity_type == ORDER_CONFIRMATION_ENTITY_TYPE,
            EmailDelivery.related_entity_id == str(order_id),
        )
        .order_by(
            EmailDelivery.created_at.desc(),
            EmailDelivery.id.desc(),
        )
        .limit(1)
    )


def _successful_order_confirmation_delivery(
    db: Session,
    *,
    order_id: uuid.UUID,
) -> EmailDelivery | None:
    return db.scalar(
        select(EmailDelivery)
        .where(
            EmailDelivery.category == ORDER_CONFIRMATION_CATEGORY,
            EmailDelivery.related_entity_type == ORDER_CONFIRMATION_ENTITY_TYPE,
            EmailDelivery.related_entity_id == str(order_id),
            EmailDelivery.status == EmailDeliveryStatus.sent,
        )
        .order_by(
            EmailDelivery.sent_at.desc(),
            EmailDelivery.created_at.desc(),
        )
        .limit(1)
    )


def send_order_confirmation(
    db: Session,
    *,
    order: Order,
    customer: User,
    settings: EmailRuntimeSettings,
    actor_user_id: uuid.UUID,
) -> EmailDelivery:
    """Send the initial staff-controlled customer Order Confirmed message.

    Supplier confirmation changes order lifecycle/cancellation state, but never
    sends this email automatically. Staff must invoke this service explicitly.
    Failed or suppressed attempts may be retried; a successful send is one-time.
    """

    if not supplier_confirmation_recorded(order):
        raise OrderConfirmationError(
            "Order Confirmed can be sent only after Supplier Confirmed is recorded."
        )
    if not order_review_completed(order):
        raise OrderConfirmationError(
            "Order Confirmed can be sent only after Order Reviewed is complete."
        )
    if order_review_on_hold(order):
        raise OrderConfirmationError(
            "Order Confirmed cannot be sent while the order is on hold pending customer response."
        )

    stage = customer_order_stage(order)
    if stage in {
        CustomerOrderStage.cancelled,
        CustomerOrderStage.refunded,
    }:
        raise OrderConfirmationError(
            "Order Confirmed cannot be sent for a cancelled or refunded order."
        )

    existing = _successful_order_confirmation_delivery(
        db,
        order_id=order.id,
    )
    if existing is not None:
        raise OrderConfirmationError(
            "Order Confirmed has already been sent successfully for this order."
        )

    order_id = str(order.id)
    safe_order_id = escape(order_id)

    delivery = deliver_email(
        db,
        settings=settings,
        message=EmailMessage(
            sender=settings.email_from,
            recipient=customer.email,
            subject="Order Confirmed",
            body_text=(
                "Order Confirmed\n\n"
                "Your D'Acqua Dolce order has been reviewed and is confirmed.\n"
                f"Order ID: {order_id}\n\n"
                "Please keep this message for your records."
            ),
            body_html=(
                "<h1>Order Confirmed</h1>"
                "<p>Your D&apos;Acqua Dolce order has been reviewed and is confirmed.</p>"
                f"<p><strong>Order ID:</strong> {safe_order_id}</p>"
                "<p>Please keep this message for your records.</p>"
            ),
        ),
        category=ORDER_CONFIRMATION_CATEGORY,
        related_entity_type=ORDER_CONFIRMATION_ENTITY_TYPE,
        related_entity_id=order_id,
        customer_user_id=customer.id,
        author_user_id=actor_user_id,
    )

    record_audit_event(
        db,
        action="order.confirmation_delivery",
        entity_type="order",
        entity_id=order_id,
        actor_user_id=actor_user_id,
        metadata={
            "delivery_id": str(delivery.id),
            "delivery_status": delivery.status.value,
        },
    )

    db.flush()
    return delivery

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.email_config import EmailRuntimeSettings
from app.integrations.email import EmailMessage
from app.models.catalog import (
    InventoryStatus,
    Product,
    ProductLifecycleStatus,
    StockNotificationSubscription,
)
from app.models.email import EmailDeliveryStatus
from app.services.audit import record_audit_event
from app.services.email_delivery import deliver_email


@dataclass(frozen=True, slots=True)
class StockNotificationDispatchSummary:
    attempted: int = 0
    sent: int = 0
    failed: int = 0
    suppressed: int = 0


def inventory_is_staff_confirmed_available(
    *,
    status: InventoryStatus,
    quantity_on_hand: int,
    quantity_reserved: int,
    lifecycle_status: ProductLifecycleStatus,
) -> bool:
    """Return whether a staff inventory save confirms customer-available stock."""

    if lifecycle_status == ProductLifecycleStatus.discontinued:
        return False

    if status not in {
        InventoryStatus.in_stock,
        InventoryStatus.low_stock,
    }:
        return False

    return quantity_on_hand > max(quantity_reserved, 0)


def dispatch_back_in_stock_notifications(
    db: Session,
    *,
    product: Product,
    settings: EmailRuntimeSettings,
    actor_user_id: uuid.UUID | None,
) -> StockNotificationDispatchSummary:
    """Send one-time notices for active subscriptions for an available product.

    Successful delivery completes the subscription. Failed or suppressed
    delivery leaves it active so a later staff-confirmed inventory save can
    retry it. The product inventory row is locked by the caller, which
    serializes concurrent staff confirmation for the same product.
    """

    subscriptions = db.scalars(
        select(StockNotificationSubscription)
        .where(
            StockNotificationSubscription.product_id == product.id,
            StockNotificationSubscription.active.is_(True),
        )
        .order_by(StockNotificationSubscription.created_at)
        .with_for_update()
    ).all()

    attempted = 0
    sent = 0
    failed = 0
    suppressed = 0
    product_url = settings.public_url(product.public_path)
    safe_name = escape(product.name)
    safe_url = escape(product_url, quote=True)

    for subscription in subscriptions:
        attempted += 1
        delivery = deliver_email(
            db,
            settings=settings,
            message=EmailMessage(
                sender=settings.email_from,
                recipient=subscription.email,
                subject=f"{product.name} is available again",
                body_text=(
                    "You asked D'Acqua Dolce to notify you when "
                    f"{product.name} became available again.\n\n"
                    "Staff has confirmed current availability.\n"
                    f"View the system:\n{product_url}\n\n"
                    "This is a one-time availability notice. "
                    "After a successful send, your request is complete. "
                    "Availability can change before purchase."
                ),
                body_html=(
                    "<p>You asked D&apos;Acqua Dolce to notify you when "
                    f"<strong>{safe_name}</strong> became available again.</p>"
                    "<p>Staff has confirmed current availability.</p>"
                    f'<p><a href="{safe_url}">View the system</a></p>'
                    "<p>This is a one-time availability notice. "
                    "After a successful send, your request is complete. "
                    "Availability can change before purchase.</p>"
                ),
            ),
            category="stock_notification",
            related_entity_type="stock_notification_subscription",
            related_entity_id=str(subscription.id),
        )

        if delivery.status == EmailDeliveryStatus.sent:
            subscription.active = False
            subscription.notified_at = datetime.now(UTC)
            sent += 1
        elif delivery.status == EmailDeliveryStatus.suppressed:
            suppressed += 1
        else:
            failed += 1

        record_audit_event(
            db,
            action="catalog.stock_notification_delivery",
            entity_type="stock_notification_subscription",
            entity_id=str(subscription.id),
            actor_user_id=actor_user_id,
            metadata={
                "product_id": str(product.id),
                "sku": product.sku,
                "delivery_id": str(delivery.id),
                "delivery_status": delivery.status.value,
            },
        )

    db.flush()

    return StockNotificationDispatchSummary(
        attempted=attempted,
        sent=sent,
        failed=failed,
        suppressed=suppressed,
    )

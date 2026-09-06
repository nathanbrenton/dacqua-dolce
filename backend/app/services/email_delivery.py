from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.email_config import (
    EmailRuntimeSettings,
)
from app.integrations.email import (
    EmailMessage,
)
from app.integrations.postmark import (
    PostmarkEmailProvider,
)
from app.models.email import (
    EmailDelivery,
    EmailDeliveryStatus,
)


def deliver_email(
    db: Session,
    *,
    settings: EmailRuntimeSettings,
    message: EmailMessage,
    category: str,
    related_entity_type: (str | None) = None,
    related_entity_id: (str | None) = None,
) -> EmailDelivery:
    delivery = EmailDelivery(
        category=category,
        related_entity_type=(related_entity_type),
        related_entity_id=(related_entity_id),
        provider=(settings.email_provider),
        sender=message.sender,
        recipient=message.recipient,
        subject=message.subject,
        status=(EmailDeliveryStatus.pending),
    )

    db.add(delivery)
    db.flush()

    if settings.email_provider == "disabled":
        delivery.status = EmailDeliveryStatus.suppressed
        delivery.error_summary = "Email provider disabled."
        db.flush()

        return delivery

    token = settings.postmark_token_value

    if token is None:
        delivery.status = EmailDeliveryStatus.failed
        delivery.error_summary = "Postmark server token not configured."
        db.flush()

        return delivery

    try:
        result = PostmarkEmailProvider(
            server_token=token,
        ).send(message)
    except Exception as exc:
        # Never persist provider payloads or
        # message bodies. Keep the failure
        # description bounded.
        delivery.status = EmailDeliveryStatus.failed
        delivery.error_summary = str(exc)[:500]
    else:
        delivery.status = EmailDeliveryStatus.sent
        delivery.provider_reference = result.provider_reference
        delivery.sent_at = datetime.now(UTC)

    db.flush()

    return delivery

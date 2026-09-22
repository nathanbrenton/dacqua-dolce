import uuid
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
from app.models.communications import (
    CommunicationMessageStatus,
    CommunicationThread,
)
from app.models.email import (
    EmailDelivery,
    EmailDeliveryStatus,
)
from app.services.communications_archive import (
    archive_outbound_email,
)


def deliver_email(
    db: Session,
    *,
    settings: EmailRuntimeSettings,
    message: EmailMessage,
    category: str,
    related_entity_type: (str | None) = None,
    related_entity_id: (str | None) = None,
    customer_user_id: uuid.UUID | None = None,
    communication_thread: CommunicationThread | None = None,
    author_user_id: uuid.UUID | None = None,
    archive_sensitive_values: tuple[str, ...] = (),
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

    archived_message = archive_outbound_email(
        db,
        delivery=delivery,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        customer_user_id=customer_user_id,
        communication_thread=communication_thread,
        author_user_id=author_user_id,
        sensitive_values=archive_sensitive_values,
    )

    if settings.email_provider == "disabled":
        delivery.status = EmailDeliveryStatus.suppressed
        delivery.error_summary = "Email provider disabled."
        archived_message.status = (
            CommunicationMessageStatus.suppressed
        )
        db.flush()

        return delivery

    token = settings.postmark_token_value

    if token is None:
        delivery.status = EmailDeliveryStatus.failed
        delivery.error_summary = "Postmark server token not configured."
        archived_message.status = CommunicationMessageStatus.failed
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
        archived_message.status = CommunicationMessageStatus.failed
    else:
        sent_at = datetime.now(UTC)
        delivery.status = EmailDeliveryStatus.sent
        delivery.provider_reference = result.provider_reference
        delivery.sent_at = sent_at
        archived_message.status = CommunicationMessageStatus.sent
        archived_message.provider_message_id = result.provider_reference
        archived_message.sent_at = sent_at

    db.flush()

    return delivery

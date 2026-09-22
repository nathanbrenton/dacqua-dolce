import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.integrations.email import EmailMessage
from app.models.communications import (
    CommunicationDirection,
    CommunicationMessage,
    CommunicationMessageStatus,
    CommunicationRecipient,
    CommunicationRecipientType,
    CommunicationThread,
    CommunicationThreadStatus,
)
from app.models.email import EmailDelivery

REDACTED_ARCHIVE_VALUE = "[REDACTED]"


def _redact_value(
    value: str | None,
    *,
    sensitive_values: tuple[str, ...],
) -> tuple[str | None, bool]:
    if value is None:
        return None, False

    redacted = value
    changed = False

    for sensitive_value in sensitive_values:
        if not sensitive_value:
            continue

        if sensitive_value in redacted:
            redacted = redacted.replace(
                sensitive_value,
                REDACTED_ARCHIVE_VALUE,
            )
            changed = True

    return redacted, changed


def archive_outbound_email(
    db: Session,
    *,
    delivery: EmailDelivery,
    message: EmailMessage,
    related_entity_type: str | None,
    related_entity_id: str | None,
    customer_user_id: uuid.UUID | None = None,
    sensitive_values: tuple[str, ...] = (),
) -> CommunicationMessage:
    archived_subject, subject_redacted = _redact_value(
        message.subject,
        sensitive_values=sensitive_values,
    )
    archived_text, text_redacted = _redact_value(
        message.body_text,
        sensitive_values=sensitive_values,
    )
    archived_html, html_redacted = _redact_value(
        message.body_html,
        sensitive_values=sensitive_values,
    )

    now = datetime.now(UTC)

    thread = CommunicationThread(
        customer_user_id=customer_user_id,
        subject=archived_subject,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        status=CommunicationThreadStatus.open,
        last_message_at=now,
    )
    db.add(thread)
    db.flush()

    archived_message = CommunicationMessage(
        thread_id=thread.id,
        email_delivery_id=delivery.id,
        direction=CommunicationDirection.outbound,
        status=CommunicationMessageStatus.queued,
        provider=delivery.provider,
        message_stream="outbound",
        sender_address=message.sender,
        subject=archived_subject or "",
        body_text=archived_text,
        body_html=archived_html,
        content_redacted=(
            subject_redacted
            or text_redacted
            or html_redacted
        ),
    )
    db.add(archived_message)
    db.flush()

    db.add(
        CommunicationRecipient(
            message_id=archived_message.id,
            recipient_type=CommunicationRecipientType.to,
            address=message.recipient,
            position=0,
        )
    )
    db.flush()

    return archived_message

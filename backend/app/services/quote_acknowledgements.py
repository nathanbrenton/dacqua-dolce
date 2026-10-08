"""Transactional, cross-worker limits for unsolicited quote acknowledgement mail.

Uses existing email delivery evidence and PostgreSQL advisory transaction lock.
Run in the same transaction as the quote and delivery write.
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.email import normalize_email_address
from app.core.email_config import EmailRuntimeSettings
from app.integrations.email import EmailMessage
from app.models.email import EmailDelivery, EmailDeliveryStatus
from app.services.email_delivery import deliver_email

CATEGORY = "quote_customer_receipt"
# Fixed application-wide key; serializes all quote acknowledgement decisions.
LOCK_KEY = 762301337104


def deliver_quote_acknowledgement(
    db: Session,
    *,
    settings: EmailRuntimeSettings,
    quote_id: str,
    recipient: str,
    customer_user_id=None,
) -> EmailDelivery:
    normalized = normalize_email_address(recipient)
    message = EmailMessage(
        sender=settings.email_from,
        recipient=normalized,
        subject="We received your D'Acqua Dolce request",
        body_text=(
            "Thank you for contacting D'Acqua Dolce.\n\n"
            "Your request has been received.\n"
            f"Reference: {quote_id}\n\n"
            "A team member may follow up using the contact "
            "information you provided."
        ),
    )
    # The DB lock is held through provider send and transaction commit.
    # This prioritizes strict quota enforcement over email throughput.
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": LOCK_KEY})
    reason = None
    if not settings.quote_ack_enabled:
        reason = "acknowledgements_disabled"
    elif not settings.quote_ack_message_stream:
        reason = "acknowledgement_stream_unconfigured"
    else:
        now = datetime.now(UTC)
        recent = select(func.count(EmailDelivery.id)).where(
            EmailDelivery.category == CATEGORY,
            EmailDelivery.status != EmailDeliveryStatus.suppressed,
        )
        prior = db.scalar(recent.where(
            EmailDelivery.recipient == normalized,
            EmailDelivery.created_at >= now - timedelta(
                hours=settings.quote_ack_recipient_cooldown_hours
            ),
        )) or 0
        global_count = db.scalar(recent.where(
            EmailDelivery.created_at >= now - timedelta(hours=1)
        )) or 0
        if prior:
            reason = "recipient_cooldown"
        elif global_count >= settings.quote_ack_global_limit_per_hour:
            reason = "global_acknowledgement_limit"

    if reason is not None:
        disabled = settings.model_copy(update={"email_provider": "disabled"})
        delivery = deliver_email(
            db, settings=disabled, message=message, category=CATEGORY,
            related_entity_type="quote_request", related_entity_id=quote_id,
            customer_user_id=customer_user_id,
        )
        delivery.error_summary = reason
        db.flush()
        return delivery

    return deliver_email(
        db, settings=settings, message=message, category=CATEGORY,
        related_entity_type="quote_request", related_entity_id=quote_id,
        customer_user_id=customer_user_id,
        message_stream=settings.quote_ack_message_stream,
    )

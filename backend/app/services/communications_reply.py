import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.email import normalize_email_address
from app.core.email_config import EmailRuntimeSettings
from app.integrations.email import EmailMessage
from app.models.communications import (
    CommunicationDirection,
    CommunicationMessage,
    CommunicationRecipient,
    CommunicationRecipientType,
    CommunicationThread,
)
from app.models.email import EmailDelivery
from app.models.identity import User
from app.services.email_delivery import deliver_email


class CommunicationReplyRecipientUnavailable(RuntimeError):
    pass


class CommunicationReplyConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommunicationReplyResult:
    delivery: EmailDelivery
    recipient: str


def _normalized_address(value: str | None) -> str | None:
    if value is None:
        return None

    try:
        return normalize_email_address(value)
    except ValueError:
        return None


def resolve_communication_reply_target(
    db: Session,
    *,
    thread: CommunicationThread,
) -> str | None:
    latest_inbound_sender = db.scalar(
        select(CommunicationMessage.sender_address)
        .where(
            CommunicationMessage.thread_id == thread.id,
            CommunicationMessage.direction
            == CommunicationDirection.inbound,
        )
        .order_by(
            CommunicationMessage.created_at.desc(),
            CommunicationMessage.id.desc(),
        )
        .limit(1)
    )

    target = _normalized_address(latest_inbound_sender)
    if target is not None:
        return target

    if thread.customer_user_id is not None:
        customer_email = db.scalar(
            select(User.email).where(
                User.id == thread.customer_user_id
            )
        )
        target = _normalized_address(customer_email)
        if target is not None:
            return target

    latest_outbound_recipient = db.scalar(
        select(CommunicationRecipient.address)
        .join(
            CommunicationMessage,
            CommunicationMessage.id
            == CommunicationRecipient.message_id,
        )
        .where(
            CommunicationMessage.thread_id == thread.id,
            CommunicationMessage.direction
            == CommunicationDirection.outbound,
            CommunicationRecipient.recipient_type
            == CommunicationRecipientType.to,
        )
        .order_by(
            CommunicationMessage.created_at.desc(),
            CommunicationRecipient.position,
            CommunicationRecipient.id,
        )
        .limit(1)
    )

    return _normalized_address(latest_outbound_recipient)


def _reply_subject(
    db: Session,
    *,
    thread: CommunicationThread,
) -> str:
    subject = (thread.subject or "").strip()

    if not subject:
        subject = (
            db.scalar(
                select(CommunicationMessage.subject)
                .where(CommunicationMessage.thread_id == thread.id)
                .order_by(
                    CommunicationMessage.created_at.desc(),
                    CommunicationMessage.id.desc(),
                )
                .limit(1)
            )
            or "D'Acqua Dolce message"
        ).strip()

    if subject.casefold().startswith("re:"):
        return subject[:300]

    return f"Re: {subject}"[:300]


def send_communication_reply(
    db: Session,
    *,
    settings: EmailRuntimeSettings,
    thread: CommunicationThread,
    author_user_id: uuid.UUID,
    body_text: str,
) -> CommunicationReplyResult:
    recipient = resolve_communication_reply_target(
        db,
        thread=thread,
    )

    if recipient is None:
        raise CommunicationReplyRecipientUnavailable(
            "No customer reply address is available for this conversation."
        )

    reply_to = settings.postmark_thread_reply_to(thread.id)

    if settings.email_provider == "postmark" and reply_to is None:
        raise CommunicationReplyConfigurationError(
            "Postmark inbound address is not configured for threaded replies."
        )

    delivery = deliver_email(
        db,
        settings=settings,
        message=EmailMessage(
            sender=(settings.email_support_from or settings.email_from),
            recipient=recipient,
            subject=_reply_subject(db, thread=thread),
            body_text=body_text,
            reply_to=reply_to,
        ),
        category="customer_communication_reply",
        related_entity_type=thread.related_entity_type,
        related_entity_id=thread.related_entity_id,
        customer_user_id=thread.customer_user_id,
        communication_thread=thread,
        author_user_id=author_user_id,
    )

    return CommunicationReplyResult(
        delivery=delivery,
        recipient=recipient,
    )

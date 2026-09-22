import base64
import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parseaddr

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.email import normalize_email_address
from app.integrations.email import EmailMessage
from app.models.communications import (
    CommunicationAttachment,
    CommunicationDirection,
    CommunicationEvent,
    CommunicationMessage,
    CommunicationMessageStatus,
    CommunicationRecipient,
    CommunicationRecipientType,
    CommunicationThread,
    CommunicationThreadStatus,
)
from app.models.email import EmailDelivery
from app.models.identity import User
from app.schemas.postmark_webhooks import PostmarkInboundWebhook

REDACTED_ARCHIVE_VALUE = "[REDACTED]"
MAX_INBOUND_ATTACHMENT_BYTES = 35 * 1024 * 1024


@dataclass(frozen=True)
class InboundArchiveResult:
    message: CommunicationMessage
    duplicate: bool


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


def _header_value(
    payload: PostmarkInboundWebhook,
    name: str,
) -> str | None:
    target = name.casefold()

    for header in payload.headers:
        if header.name.casefold() == target:
            value = header.value.strip()
            return value or None

    return None


def _normalize_optional_email(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    _, parsed_address = parseaddr(stripped)
    candidate = parsed_address or stripped

    try:
        return normalize_email_address(candidate)
    except ValueError:
        return candidate.strip().lower()


def _customer_user_id_for_sender(
    db: Session,
    sender: str,
) -> uuid.UUID | None:
    normalized = _normalize_optional_email(sender)
    if normalized is None:
        return None

    user = db.scalar(
        select(User).where(
            User.email == normalized,
        )
    )

    return user.id if user is not None else None


def _thread_from_mailbox_hash(
    db: Session,
    mailbox_hash: str,
) -> CommunicationThread | None:
    candidate = mailbox_hash.strip()
    if not candidate:
        return None

    try:
        thread_id = uuid.UUID(candidate)
    except ValueError:
        return None

    return db.get(CommunicationThread, thread_id)


def _thread_from_in_reply_to(
    db: Session,
    in_reply_to: str | None,
) -> CommunicationThread | None:
    if in_reply_to is None:
        return None

    prior_message = db.scalar(
        select(CommunicationMessage).where(
            CommunicationMessage.internet_message_id
            == in_reply_to,
        )
    )

    if prior_message is None:
        return None

    return db.get(
        CommunicationThread,
        prior_message.thread_id,
    )


def _resolve_inbound_thread(
    db: Session,
    *,
    payload: PostmarkInboundWebhook,
    in_reply_to: str | None,
    customer_user_id: uuid.UUID | None,
    now: datetime,
) -> CommunicationThread:
    thread = _thread_from_mailbox_hash(
        db,
        payload.mailbox_hash,
    )

    if thread is None:
        thread = _thread_from_in_reply_to(
            db,
            in_reply_to,
        )

    if thread is None:
        thread = CommunicationThread(
            customer_user_id=customer_user_id,
            subject=payload.subject or None,
            status=CommunicationThreadStatus.open,
            last_message_at=now,
        )
        db.add(thread)
        db.flush()
        return thread

    if thread.customer_user_id is None and customer_user_id is not None:
        thread.customer_user_id = customer_user_id

    thread.status = CommunicationThreadStatus.open
    thread.last_message_at = now
    return thread


def _add_inbound_recipients(
    db: Session,
    *,
    message_id: uuid.UUID,
    payload: PostmarkInboundWebhook,
) -> None:
    recipient_sets = (
        (CommunicationRecipientType.to, payload.to_full),
        (CommunicationRecipientType.cc, payload.cc_full),
        (CommunicationRecipientType.bcc, payload.bcc_full),
    )

    for recipient_type, addresses in recipient_sets:
        seen: set[str] = set()

        for position, address in enumerate(addresses):
            normalized = _normalize_optional_email(address.email)
            if normalized is None or normalized in seen:
                continue

            seen.add(normalized)
            db.add(
                CommunicationRecipient(
                    message_id=message_id,
                    recipient_type=recipient_type,
                    address=normalized,
                    display_name=address.name.strip() or None,
                    position=position,
                )
            )

    reply_to = _normalize_optional_email(payload.reply_to)
    if reply_to is not None:
        db.add(
            CommunicationRecipient(
                message_id=message_id,
                recipient_type=CommunicationRecipientType.reply_to,
                address=reply_to,
                position=0,
            )
        )


def _add_inbound_attachments(
    db: Session,
    *,
    message_id: uuid.UUID,
    payload: PostmarkInboundWebhook,
) -> None:
    cumulative_size = 0

    for attachment in payload.attachments:
        try:
            content = base64.b64decode(
                attachment.content,
                validate=True,
            )
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError(
                f"Attachment {attachment.name!r} is not valid base64."
            ) from exc

        if len(content) != attachment.content_length:
            raise ValueError(
                f"Attachment {attachment.name!r} length does not match ContentLength."
            )

        cumulative_size += len(content)
        if cumulative_size > MAX_INBOUND_ATTACHMENT_BYTES:
            raise ValueError(
                "Inbound attachments exceed the 35 MiB archive limit."
            )

        db.add(
            CommunicationAttachment(
                message_id=message_id,
                filename=attachment.name,
                content_type=attachment.content_type,
                content_id=(attachment.content_id or None),
                content_disposition=(attachment.content_disposition or None),
                size_bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                content=content,
            )
        )


def archive_postmark_inbound_email(
    db: Session,
    *,
    payload: PostmarkInboundWebhook,
) -> InboundArchiveResult:
    existing = db.scalar(
        select(CommunicationMessage).where(
            CommunicationMessage.provider == "postmark",
            CommunicationMessage.provider_message_id
            == payload.message_id,
        )
    )

    if existing is not None:
        return InboundArchiveResult(
            message=existing,
            duplicate=True,
        )

    now = datetime.now(UTC)
    in_reply_to = _header_value(
        payload,
        "In-Reply-To",
    )
    internet_message_id = _header_value(
        payload,
        "Message-ID",
    )
    sender_address = _normalize_optional_email(
        payload.from_full.email or payload.from_address
    )

    if sender_address is None:
        raise ValueError("Inbound sender address is required.")

    customer_user_id = _customer_user_id_for_sender(
        db,
        sender_address,
    )

    thread = _resolve_inbound_thread(
        db,
        payload=payload,
        in_reply_to=in_reply_to,
        customer_user_id=customer_user_id,
        now=now,
    )

    archived_message = CommunicationMessage(
        thread_id=thread.id,
        direction=CommunicationDirection.inbound,
        status=CommunicationMessageStatus.received,
        provider="postmark",
        provider_message_id=payload.message_id,
        message_stream=payload.message_stream,
        internet_message_id=internet_message_id,
        in_reply_to=in_reply_to,
        sender_address=sender_address,
        sender_name=(payload.from_full.name.strip() or payload.from_name.strip() or None),
        subject=payload.subject,
        body_text=(payload.text_body or None),
        body_html=(payload.html_body or None),
        content_redacted=False,
        received_at=now,
    )
    db.add(archived_message)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        concurrent = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.provider == "postmark",
                CommunicationMessage.provider_message_id
                == payload.message_id,
            )
        )
        if concurrent is None:
            raise

        return InboundArchiveResult(
            message=concurrent,
            duplicate=True,
        )

    _add_inbound_recipients(
        db,
        message_id=archived_message.id,
        payload=payload,
    )
    _add_inbound_attachments(
        db,
        message_id=archived_message.id,
        payload=payload,
    )

    event_fingerprint = hashlib.sha256(
        payload.message_id.encode("utf-8")
    ).hexdigest()
    db.add(
        CommunicationEvent(
            message_id=archived_message.id,
            provider="postmark",
            event_type="inbound_received",
            provider_event_id=f"inbound:{event_fingerprint}",
            occurred_at=now,
            details={
                "date": payload.date or None,
                "original_recipient": payload.original_recipient or None,
                "mailbox_hash": payload.mailbox_hash or None,
                "tag": payload.tag or None,
                "stripped_text_reply": payload.stripped_text_reply or None,
                "headers": [
                    {"name": header.name, "value": header.value}
                    for header in payload.headers
                ],
                "raw_email_present": payload.raw_email is not None,
                "attachments": [
                    {
                        "name": attachment.name,
                        "content_type": attachment.content_type,
                        "content_length": attachment.content_length,
                        "content_id": attachment.content_id,
                    }
                    for attachment in payload.attachments
                ],
            },
        )
    )
    db.flush()

    return InboundArchiveResult(
        message=archived_message,
        duplicate=False,
    )

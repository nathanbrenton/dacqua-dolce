from uuid import uuid4

from pydantic import SecretStr
from sqlalchemy import select

from app.core.email_config import EmailRuntimeSettings
from app.db.session import SessionLocal
from app.integrations.email import EmailMessage, EmailSendResult
from app.integrations.postmark import PostmarkEmailProvider
from app.models.communications import (
    CommunicationMessage,
    CommunicationMessageStatus,
    CommunicationRecipient,
    CommunicationRecipientType,
    CommunicationThread,
)
from app.models.email import EmailDeliveryStatus
from app.services.email_delivery import deliver_email


def disabled_settings() -> EmailRuntimeSettings:
    return EmailRuntimeSettings(
        public_origin="http://127.0.0.1:5173",
        email_provider="disabled",
        email_from="no-reply@example.test",
    )


def test_suppressed_email_is_archived_with_body_and_recipient() -> None:
    related_id = str(uuid4())

    with SessionLocal() as db:
        delivery = deliver_email(
            db,
            settings=disabled_settings(),
            message=EmailMessage(
                sender="no-reply@example.test",
                recipient="customer@example.test",
                subject="Account update",
                body_text="Your account was updated.",
                body_html="<p>Your account was updated.</p>",
            ),
            category="account_update",
            related_entity_type="user",
            related_entity_id=related_id,
        )

        archived = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.email_delivery_id == delivery.id
            )
        )

        assert archived is not None
        assert delivery.status == EmailDeliveryStatus.suppressed
        assert archived.status == CommunicationMessageStatus.suppressed
        assert archived.direction.value == "outbound"
        assert archived.message_stream == "outbound"
        assert archived.body_text == "Your account was updated."
        assert archived.body_html == "<p>Your account was updated.</p>"
        assert archived.content_redacted is False

        thread = db.get(CommunicationThread, archived.thread_id)
        assert thread is not None
        assert thread.related_entity_type == "user"
        assert thread.related_entity_id == related_id

        recipient = db.scalar(
            select(CommunicationRecipient).where(
                CommunicationRecipient.message_id == archived.id
            )
        )
        assert recipient is not None
        assert recipient.recipient_type == CommunicationRecipientType.to
        assert recipient.address == "customer@example.test"

        db.rollback()


def test_sensitive_values_are_redacted_only_in_archive() -> None:
    secret = "single-use-secret-value"
    original = EmailMessage(
        sender="no-reply@example.test",
        recipient="customer@example.test",
        subject=f"Subject {secret}",
        body_text=f"Open https://example.test/verify/{secret}",
        body_html=f'<a href="https://example.test/verify/{secret}">Verify</a>',
    )

    with SessionLocal() as db:
        delivery = deliver_email(
            db,
            settings=disabled_settings(),
            message=original,
            category="email_verification",
            related_entity_type="user",
            related_entity_id=str(uuid4()),
            archive_sensitive_values=(secret,),
        )

        archived = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.email_delivery_id == delivery.id
            )
        )

        assert archived is not None
        assert archived.content_redacted is True

        archived_values = (
            archived.subject,
            archived.body_text or "",
            archived.body_html or "",
        )
        assert all(secret not in value for value in archived_values)
        assert all("[REDACTED]" in value for value in archived_values)

        assert secret in original.subject
        assert secret in original.body_text
        assert secret in (original.body_html or "")

        db.rollback()


def test_postmark_success_updates_archived_message(monkeypatch) -> None:
    reference = "postmark-message-id"

    def fake_send(
        self: PostmarkEmailProvider,
        message: EmailMessage,
    ) -> EmailSendResult:
        return EmailSendResult(provider_reference=reference)

    monkeypatch.setattr(PostmarkEmailProvider, "send", fake_send)

    settings = EmailRuntimeSettings(
        public_origin="https://example.test",
        email_provider="postmark",
        postmark_server_token=SecretStr("test-token"),
        email_from="no-reply@example.test",
    )

    with SessionLocal() as db:
        delivery = deliver_email(
            db,
            settings=settings,
            message=EmailMessage(
                sender=settings.email_from,
                recipient="customer@example.test",
                subject="Sent message",
                body_text="Delivery body",
            ),
            category="test_message",
        )

        archived = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.email_delivery_id == delivery.id
            )
        )

        assert archived is not None
        assert delivery.status == EmailDeliveryStatus.sent
        assert delivery.provider_reference == reference
        assert delivery.sent_at is not None
        assert archived.status == CommunicationMessageStatus.sent
        assert archived.provider == "postmark"
        assert archived.provider_message_id == reference
        assert archived.sent_at == delivery.sent_at

        db.rollback()


def test_postmark_failure_marks_archived_message_failed(monkeypatch) -> None:
    def fake_send(
        self: PostmarkEmailProvider,
        message: EmailMessage,
    ) -> EmailSendResult:
        raise RuntimeError("provider failure")

    monkeypatch.setattr(PostmarkEmailProvider, "send", fake_send)

    settings = EmailRuntimeSettings(
        public_origin="https://example.test",
        email_provider="postmark",
        postmark_server_token=SecretStr("test-token"),
        email_from="no-reply@example.test",
    )

    with SessionLocal() as db:
        delivery = deliver_email(
            db,
            settings=settings,
            message=EmailMessage(
                sender=settings.email_from,
                recipient="customer@example.test",
                subject="Failed message",
                body_text="Delivery body",
            ),
            category="test_message",
        )

        archived = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.email_delivery_id == delivery.id
            )
        )

        assert archived is not None
        assert delivery.status == EmailDeliveryStatus.failed
        assert delivery.error_summary == "provider failure"
        assert archived.status == CommunicationMessageStatus.failed
        assert archived.provider_message_id is None
        assert archived.sent_at is None

        db.rollback()

"""The customer conversation shown inside an Operations request."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import operations
from app.core.email_config import EmailRuntimeSettings
from app.db.session import SessionLocal
from app.models.communications import (
    CommunicationDirection,
    CommunicationMessage,
    CommunicationMessageStatus,
    CommunicationThread,
    CommunicationThreadStatus,
)
from app.models.email import EmailDelivery, EmailDeliveryStatus
from app.models.identity import User
from app.models.quote import QuoteRequest
from app.schemas.operations import OperationsCommunicationReplyCreate


def _allow_operations(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        operations,
        "require_operations",
        lambda db, user: None,
    )


def _current_user() -> object:
    return SimpleNamespace(id=uuid.uuid4())


def _disable_live_email(monkeypatch: Any, db: Session) -> None:
    monkeypatch.setattr(
        operations,
        "get_email_runtime_settings",
        lambda: EmailRuntimeSettings(
            email_provider="disabled",
            email_from="no-reply@dacquadolce.com",
            email_support_from="support@dacquadolce.com",
            email_reply_from_addresses=(
                "sales@dacquadolce.com,support@dacquadolce.com"
            ),
            postmark_inbound_address="abc123@inbound.postmarkapp.com",
        ),
    )
    monkeypatch.setattr(db, "commit", lambda: db.flush())


def _quote(db: Session) -> QuoteRequest:
    quote = QuoteRequest(
        name="Customer Example",
        email=f"Quote-{uuid.uuid4()}@Example.test",
        message="Hard water spots on the glasses",
    )
    db.add(quote)
    db.flush()
    return quote


def _linked_threads(db: Session, quote: QuoteRequest) -> int:
    return db.scalar(
        select(func.count())
        .select_from(CommunicationThread)
        .where(
            CommunicationThread.related_entity_type == "quote_request",
            CommunicationThread.related_entity_id == str(quote.id),
        )
    ) or 0


def _add_operator_alert_thread(db: Session, quote: QuoteRequest) -> None:
    """A staff alert linked to the quote: a System thread, not a conversation."""
    now = datetime.now(UTC)
    delivery = EmailDelivery(
        category="quote_operator_notification",
        related_entity_type="quote_request",
        related_entity_id=str(quote.id),
        provider="disabled",
        sender="no-reply@dacquadolce.com",
        recipient="owner@example.test",
        subject="New D'Acqua Dolce quote request",
        status=EmailDeliveryStatus.suppressed,
    )
    db.add(delivery)
    db.flush()

    thread = CommunicationThread(
        subject="New D'Acqua Dolce quote request",
        related_entity_type="quote_request",
        related_entity_id=str(quote.id),
        status=CommunicationThreadStatus.open,
        last_message_at=now,
    )
    db.add(thread)
    db.flush()

    db.add(
        CommunicationMessage(
            thread_id=thread.id,
            email_delivery_id=delivery.id,
            direction=CommunicationDirection.outbound,
            status=CommunicationMessageStatus.suppressed,
            provider="disabled",
            sender_address="no-reply@dacquadolce.com",
            subject="New D'Acqua Dolce quote request",
            body_text="A new request arrived.",
            content_redacted=False,
            sent_at=now,
        )
    )
    db.flush()


def test_conversation_is_empty_but_ready_to_start(monkeypatch: Any) -> None:
    _allow_operations(monkeypatch)

    with SessionLocal() as db:
        _disable_live_email(monkeypatch, db)
        quote = _quote(db)
        _add_operator_alert_thread(db, quote)

        result = operations.get_quote_conversation(
            quote.id,
            db,  # type: ignore[arg-type]
            _current_user(),  # type: ignore[arg-type]
        )

        # The staff alert is a System thread, so there is no conversation yet.
        assert result.thread is None
        assert result.reply_target == quote.email.lower()
        assert result.reply_target_source == "quote_request"
        assert result.reply_sender_default == "sales@dacquadolce.com"
        assert "support@dacquadolce.com" in result.reply_sender_addresses

        db.rollback()


def test_first_reply_starts_a_linked_conversation_and_later_replies_reuse_it(
    monkeypatch: Any,
) -> None:
    _allow_operations(monkeypatch)

    with SessionLocal() as db:
        _disable_live_email(monkeypatch, db)
        employee = User(email=f"employee-{uuid.uuid4()}@example.test")
        db.add(employee)
        db.flush()
        quote = _quote(db)
        _add_operator_alert_thread(db, quote)

        first = operations.reply_to_quote_conversation(
            quote.id,
            OperationsCommunicationReplyCreate(
                body_text="Thanks for reaching out. A few questions first.",
            ),
            db,  # type: ignore[arg-type]
            employee,  # type: ignore[arg-type]
        )

        assert first.delivery_status == "suppressed"
        assert first.recipient == quote.email.lower()
        assert first.thread.related_entity_type == "quote_request"
        assert first.thread.related_entity_id == str(quote.id)
        assert first.thread.mailbox_kind == "inbox"
        assert first.thread.subject == operations.QUOTE_CONVERSATION_SUBJECT
        assert len(first.thread.messages) == 1
        assert first.thread.messages[0].sender_address == (
            "sales@dacquadolce.com"
        )

        second = operations.reply_to_quote_conversation(
            quote.id,
            OperationsCommunicationReplyCreate(body_text="One more detail."),
            db,  # type: ignore[arg-type]
            employee,  # type: ignore[arg-type]
        )

        assert second.thread.id == first.thread.id
        assert len(second.thread.messages) == 2
        # The staff alert thread plus one conversation, never a second one.
        assert _linked_threads(db, quote) == 2

        loaded = operations.get_quote_conversation(
            quote.id,
            db,  # type: ignore[arg-type]
            _current_user(),  # type: ignore[arg-type]
        )

        assert loaded.thread is not None
        assert loaded.thread.id == first.thread.id
        assert loaded.reply_target == quote.email.lower()

        db.rollback()


def test_conversation_prefers_the_existing_customer_thread(
    monkeypatch: Any,
) -> None:
    _allow_operations(monkeypatch)
    now = datetime.now(UTC)

    with SessionLocal() as db:
        _disable_live_email(monkeypatch, db)
        quote = _quote(db)

        thread = CommunicationThread(
            subject="Re: my request",
            related_entity_type="quote_request",
            related_entity_id=str(quote.id),
            status=CommunicationThreadStatus.open,
            last_message_at=now,
        )
        db.add(thread)
        db.flush()
        db.add(
            CommunicationMessage(
                thread_id=thread.id,
                direction=CommunicationDirection.inbound,
                status=CommunicationMessageStatus.received,
                provider="postmark",
                provider_message_id=f"test-{uuid.uuid4()}",
                message_stream="inbound",
                sender_address="reply-from@example.test",
                subject="Re: my request",
                body_text="Is Tuesday OK?",
                content_redacted=False,
                received_at=now,
            )
        )
        db.flush()

        result = operations.get_quote_conversation(
            quote.id,
            db,  # type: ignore[arg-type]
            _current_user(),  # type: ignore[arg-type]
        )

        assert result.thread is not None
        assert result.thread.id == str(thread.id)
        assert result.reply_target == "reply-from@example.test"
        assert result.reply_target_source == "latest_inbound_sender"

        db.rollback()


def test_missing_quote_is_not_found(monkeypatch: Any) -> None:
    _allow_operations(monkeypatch)

    with SessionLocal() as db:
        with pytest.raises(HTTPException) as excinfo:
            operations.get_quote_conversation(
                uuid.uuid4(),
                db,  # type: ignore[arg-type]
                _current_user(),  # type: ignore[arg-type]
            )

        assert excinfo.value.status_code == 404

        with pytest.raises(HTTPException) as excinfo:
            operations.reply_to_quote_conversation(
                uuid.uuid4(),
                OperationsCommunicationReplyCreate(body_text="Hello"),
                db,  # type: ignore[arg-type]
                _current_user(),  # type: ignore[arg-type]
            )

        assert excinfo.value.status_code == 404

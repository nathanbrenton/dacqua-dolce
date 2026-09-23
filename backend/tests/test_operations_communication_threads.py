import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.api import operations
from app.core.email_config import EmailRuntimeSettings
from app.db.session import SessionLocal
from app.models.communications import (
    CommunicationAttachment,
    CommunicationDirection,
    CommunicationMessage,
    CommunicationMessageStatus,
    CommunicationRecipient,
    CommunicationRecipientType,
    CommunicationThread,
    CommunicationThreadStatus,
)
from app.models.identity import User
from app.schemas.operations import (
    OperationsCommunicationReplyCreate,
    OperationsCommunicationThreadStatusUpdate,
)


def _allow_operations(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        operations,
        "require_operations",
        lambda db, user: None,
    )


def _current_user() -> object:
    return SimpleNamespace(
        id=uuid.uuid4(),
    )


def test_communication_thread_list_and_detail_expose_archive(
    monkeypatch: Any,
) -> None:
    _allow_operations(monkeypatch)
    now = datetime.now(UTC)

    with SessionLocal() as db:
        thread = CommunicationThread(
            subject="Water test follow-up",
            related_entity_type="quote_request",
            related_entity_id=str(uuid.uuid4()),
            status=CommunicationThreadStatus.open,
            last_message_at=now,
        )
        db.add(thread)
        db.flush()

        inbound = CommunicationMessage(
            thread_id=thread.id,
            direction=CommunicationDirection.inbound,
            status=CommunicationMessageStatus.received,
            provider="postmark",
            provider_message_id=f"test-{uuid.uuid4()}",
            message_stream="inbound",
            sender_address="customer@example.test",
            sender_name="Customer Example",
            subject="Water test follow-up",
            body_text="Can you tell me what happens next?",
            content_redacted=False,
            received_at=now,
        )
        db.add(inbound)
        db.flush()

        db.add(
            CommunicationRecipient(
                message_id=inbound.id,
                recipient_type=CommunicationRecipientType.to,
                address="abc123+thread-id@inbound.postmarkapp.com",
                position=0,
            )
        )
        db.add(
            CommunicationAttachment(
                message_id=inbound.id,
                filename="water-report.txt",
                content_type="text/plain",
                size_bytes=6,
                sha256="a" * 64,
                content=b"report",
            )
        )
        db.flush()

        thread_rows = operations.list_communication_threads(
            db,  # type: ignore[arg-type]
            _current_user(),  # type: ignore[arg-type]
        )
        row = next(
            item
            for item in thread_rows
            if item.id == str(thread.id)
        )

        assert row.subject == "Water test follow-up"
        assert row.status == "open"
        assert row.message_count == 1
        assert row.latest_direction == "inbound"
        assert row.latest_sender_address == "customer@example.test"
        assert row.latest_subject == "Water test follow-up"
        assert row.failed_message_count == 0

        detail = operations.get_communication_thread(
            thread.id,
            db,  # type: ignore[arg-type]
            _current_user(),  # type: ignore[arg-type]
        )

        assert detail.id == str(thread.id)
        assert len(detail.messages) == 1

        message = detail.messages[0]
        assert message.direction == "inbound"
        assert message.status == "received"
        assert message.body_text == "Can you tell me what happens next?"
        assert message.content_redacted is False
        assert message.recipients == []
        assert message.attachments[0].filename == "water-report.txt"
        assert message.attachments[0].size_bytes == 6
        assert message.attachments[0].sha256 == "a" * 64

        payload = message.model_dump()
        assert "body_html" not in payload
        assert "provider_message_id" not in payload
        assert "internet_message_id" not in payload
        assert "inbound.postmarkapp.com" not in str(payload)
        assert "content" not in payload["attachments"][0]

        db.rollback()


def test_communication_thread_detail_requires_operations_access(
    monkeypatch: Any,
) -> None:
    with SessionLocal() as db:
        thread = CommunicationThread(
            subject="Protected thread",
            status=CommunicationThreadStatus.open,
        )
        db.add(thread)
        db.flush()

        def deny(
            db: object,
            *,
            user: object,
        ) -> None:
            raise HTTPException(
                status_code=403,
                detail="Operations access required.",
            )

        monkeypatch.setattr(
            operations,
            "require_operations",
            deny,
        )

        with pytest.raises(HTTPException) as exc:
            operations.get_communication_thread(
                thread.id,
                db,  # type: ignore[arg-type]
                _current_user(),  # type: ignore[arg-type]
            )

        assert exc.value.status_code == 403
        db.rollback()


def test_missing_communication_thread_returns_404(
    monkeypatch: Any,
) -> None:
    _allow_operations(monkeypatch)

    with SessionLocal() as db:
        missing_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc:
            operations.get_communication_thread(
                missing_id,
                db,  # type: ignore[arg-type]
                _current_user(),  # type: ignore[arg-type]
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "Communication thread not found."



def test_reply_archives_into_existing_thread_without_live_email(
    monkeypatch: Any,
) -> None:
    _allow_operations(monkeypatch)
    now = datetime.now(UTC)

    with SessionLocal() as db:
        employee = User(
            email=f"employee-{uuid.uuid4()}@example.test",
        )
        db.add(employee)
        db.flush()

        thread = CommunicationThread(
            subject="Water test follow-up",
            status=CommunicationThreadStatus.open,
            last_message_at=now,
        )
        db.add(thread)
        db.flush()

        inbound = CommunicationMessage(
            thread_id=thread.id,
            direction=CommunicationDirection.inbound,
            status=CommunicationMessageStatus.received,
            provider="postmark",
            provider_message_id=f"test-{uuid.uuid4()}",
            message_stream="inbound",
            sender_address="customer@example.test",
            subject="Water test follow-up",
            body_text="Can you tell me what happens next?",
            content_redacted=False,
            received_at=now,
        )
        db.add(inbound)
        db.flush()

        monkeypatch.setattr(
            operations,
            "get_email_runtime_settings",
            lambda: EmailRuntimeSettings(
                email_provider="disabled",
                email_from="no-reply@dacquadolce.com",
                email_support_from="support@dacquadolce.com",
                postmark_inbound_address=(
                    "abc123@inbound.postmarkapp.com"
                ),
            ),
        )
        monkeypatch.setattr(
            db,
            "commit",
            lambda: db.flush(),
        )

        result = operations.reply_to_communication_thread(
            thread.id,
            OperationsCommunicationReplyCreate(
                body_text="We can help with the next step.",
            ),
            db,  # type: ignore[arg-type]
            employee,  # type: ignore[arg-type]
        )

        assert result.delivery_status == "suppressed"
        assert result.recipient == "customer@example.test"
        assert result.thread.id == str(thread.id)
        assert result.thread.reply_target == "customer@example.test"
        assert len(result.thread.messages) == 2

        reply = result.thread.messages[-1]
        assert reply.direction == "outbound"
        assert reply.status == "suppressed"
        assert reply.author_user_id == str(employee.id)
        assert reply.sender_address == "support@dacquadolce.com"
        assert reply.body_text == "We can help with the next step."
        assert reply.recipients[0].address == "customer@example.test"

        db.rollback()


def test_thread_failure_count_and_archive_restore(
    monkeypatch: Any,
) -> None:
    _allow_operations(monkeypatch)
    now = datetime.now(UTC)

    with SessionLocal() as db:
        actor = User(
            email=f"operator-{uuid.uuid4()}@example.test",
        )
        db.add(actor)
        db.flush()

        thread = CommunicationThread(
            subject="Delivery problem",
            status=CommunicationThreadStatus.open,
            last_message_at=now,
        )
        db.add(thread)
        db.flush()

        db.add(
            CommunicationMessage(
                thread_id=thread.id,
                direction=CommunicationDirection.outbound,
                status=CommunicationMessageStatus.failed,
                provider="postmark",
                provider_message_id=f"failed-{uuid.uuid4()}",
                message_stream="outbound",
                sender_address="support@dacquadolce.com",
                subject="Delivery problem",
                body_text="Test failure",
                content_redacted=False,
                created_at=now,
            )
        )
        db.flush()

        monkeypatch.setattr(
            db,
            "commit",
            lambda: db.flush(),
        )

        rows = operations.list_communication_threads(
            db,  # type: ignore[arg-type]
            actor,  # type: ignore[arg-type]
        )
        row = next(item for item in rows if item.id == str(thread.id))
        assert row.failed_message_count == 1
        assert row.status == "open"

        archived = operations.update_communication_thread_status(
            thread.id,
            OperationsCommunicationThreadStatusUpdate(status="closed"),
            db,  # type: ignore[arg-type]
            actor,  # type: ignore[arg-type]
        )
        assert archived.status == "closed"
        assert archived.failed_message_count == 1

        restored = operations.update_communication_thread_status(
            thread.id,
            OperationsCommunicationThreadStatusUpdate(status="open"),
            db,  # type: ignore[arg-type]
            actor,  # type: ignore[arg-type]
        )
        assert restored.status == "open"

        db.rollback()

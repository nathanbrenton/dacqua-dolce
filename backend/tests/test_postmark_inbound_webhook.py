import base64
import hashlib
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.email_config import get_email_runtime_settings
from app.db.session import SessionLocal
from app.main import app
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
from app.models.identity import User

client = TestClient(app)

WEBHOOK_USERNAME = "postmark-inbound"
WEBHOOK_PASSWORD = "test-webhook-password"


@pytest.fixture(autouse=True)
def inbound_webhook_credentials(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME",
        WEBHOOK_USERNAME,
    )
    monkeypatch.setenv(
        "DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD",
        WEBHOOK_PASSWORD,
    )
    get_email_runtime_settings.cache_clear()

    yield

    get_email_runtime_settings.cache_clear()


def basic_auth_header(
    username: str = WEBHOOK_USERNAME,
    password: str = WEBHOOK_PASSWORD,
) -> dict[str, str]:
    token = base64.b64encode(
        f"{username}:{password}".encode()
    ).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def inbound_payload(
    *,
    message_id: str | None = None,
    sender: str = "customer@example.test",
    mailbox_hash: str = "",
    in_reply_to: str | None = None,
    attachment_content: bytes | None = None,
) -> dict[str, object]:
    headers = [
        {
            "Name": "Message-ID",
            "Value": f"<{uuid4()}@example.test>",
        }
    ]

    if in_reply_to is not None:
        headers.append(
            {
                "Name": "In-Reply-To",
                "Value": in_reply_to,
            }
        )

    attachments: list[dict[str, object]] = []
    if attachment_content is not None:
        attachments.append(
            {
                "Name": "customer-note.txt",
                "Content": base64.b64encode(
                    attachment_content
                ).decode("ascii"),
                "ContentType": "text/plain",
                "ContentLength": len(attachment_content),
                "ContentID": "note@example.test",
            }
        )

    return {
        "FromName": "Customer Example",
        "MessageStream": "inbound",
        "From": sender,
        "FromFull": {
            "Email": sender,
            "Name": "Customer Example",
            "MailboxHash": "",
        },
        "To": '"D Acqua Dolce" <support@example.test>',
        "ToFull": [
            {
                "Email": "support@example.test",
                "Name": "D Acqua Dolce",
                "MailboxHash": mailbox_hash,
            }
        ],
        "Cc": "copy@example.test",
        "CcFull": [
            {
                "Email": "copy@example.test",
                "Name": "Copy Recipient",
                "MailboxHash": "",
            }
        ],
        "Bcc": "",
        "BccFull": [],
        "OriginalRecipient": "support@example.test",
        "Subject": "Re: Water filtration question",
        "MessageID": message_id or str(uuid4()),
        "ReplyTo": '"Customer Example" <reply@example.test>',
        "MailboxHash": mailbox_hash,
        "Date": "Tue, 22 Sep 2026 12:30:00 -0700",
        "TextBody": "Thanks for the information.",
        "HtmlBody": "<p>Thanks for the information.</p>",
        "StrippedTextReply": "Thanks for the information.",
        "Tag": "",
        "Headers": headers,
        "Attachments": attachments,
    }


def test_inbound_webhook_requires_basic_auth() -> None:
    payload = inbound_payload()

    missing = client.post(
        "/api/webhooks/postmark/inbound",
        json=payload,
    )
    assert missing.status_code == 401

    wrong = client.post(
        "/api/webhooks/postmark/inbound",
        json=payload,
        headers=basic_auth_header(password="wrong-password"),
    )
    assert wrong.status_code == 401


def test_inbound_webhook_fails_closed_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME",
        raising=False,
    )
    monkeypatch.delenv(
        "DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD",
        raising=False,
    )
    get_email_runtime_settings.cache_clear()

    response = client.post(
        "/api/webhooks/postmark/inbound",
        json=inbound_payload(),
        headers=basic_auth_header(),
    )

    assert response.status_code == 503


def test_inbound_webhook_archives_message_recipients_attachment_and_event() -> None:
    sender = f"inbound-{uuid4()}@example.test"
    message_id = str(uuid4())
    attachment_content = b"durable inbound attachment"

    with SessionLocal() as db:
        user = User(email=sender)
        db.add(user)
        db.commit()
        user_id = user.id

    response = client.post(
        "/api/webhooks/postmark/inbound",
        json=inbound_payload(
            message_id=message_id,
            sender=sender,
            attachment_content=attachment_content,
        ),
        headers=basic_auth_header(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["message_id"] == message_id

    thread_id = data["thread_id"]

    with SessionLocal() as db:
        message = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.provider == "postmark",
                CommunicationMessage.provider_message_id == message_id,
            )
        )
        assert message is not None
        assert message.direction == CommunicationDirection.inbound
        assert message.status == CommunicationMessageStatus.received
        assert message.sender_address == sender
        assert message.sender_name == "Customer Example"
        assert message.body_text == "Thanks for the information."
        assert message.body_html == "<p>Thanks for the information.</p>"
        assert message.received_at is not None
        assert message.internet_message_id is not None

        thread = db.get(CommunicationThread, message.thread_id)
        assert thread is not None
        assert str(thread.id) == thread_id
        assert thread.customer_user_id == user_id

        recipients = db.scalars(
            select(CommunicationRecipient)
            .where(CommunicationRecipient.message_id == message.id)
            .order_by(
                CommunicationRecipient.recipient_type,
                CommunicationRecipient.position,
            )
        ).all()
        assert {
            (recipient.recipient_type, recipient.address)
            for recipient in recipients
        } == {
            (CommunicationRecipientType.to, "support@example.test"),
            (CommunicationRecipientType.cc, "copy@example.test"),
            (CommunicationRecipientType.reply_to, "reply@example.test"),
        }

        attachment = db.scalar(
            select(CommunicationAttachment).where(
                CommunicationAttachment.message_id == message.id,
            )
        )
        assert attachment is not None
        assert attachment.filename == "customer-note.txt"
        assert attachment.content == attachment_content
        assert attachment.size_bytes == len(attachment_content)
        assert attachment.sha256 == hashlib.sha256(
            attachment_content
        ).hexdigest()

        event = db.scalar(
            select(CommunicationEvent).where(
                CommunicationEvent.message_id == message.id,
            )
        )
        assert event is not None
        assert event.event_type == "inbound_received"
        assert event.provider == "postmark"
        assert event.details is not None
        assert event.details["original_recipient"] == "support@example.test"
        assert event.details["raw_email_present"] is False

        db.delete(thread)
        user = db.get(User, user_id)
        if user is not None:
            db.delete(user)
        db.commit()


def test_inbound_webhook_is_idempotent_by_postmark_message_id() -> None:
    message_id = str(uuid4())
    payload = inbound_payload(message_id=message_id)

    first = client.post(
        "/api/webhooks/postmark/inbound",
        json=payload,
        headers=basic_auth_header(),
    )
    second = client.post(
        "/api/webhooks/postmark/inbound",
        json=payload,
        headers=basic_auth_header(),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "received"
    assert second.json()["status"] == "duplicate"
    assert (
        first.json()["communication_message_id"]
        == second.json()["communication_message_id"]
    )

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count(CommunicationMessage.id)).where(
                CommunicationMessage.provider == "postmark",
                CommunicationMessage.provider_message_id == message_id,
            )
        )
        assert count == 1

        message = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.provider == "postmark",
                CommunicationMessage.provider_message_id == message_id,
            )
        )
        assert message is not None
        thread = db.get(CommunicationThread, message.thread_id)
        assert thread is not None
        db.delete(thread)
        db.commit()


def test_inbound_reply_matches_existing_thread_by_in_reply_to() -> None:
    internet_message_id = f"<{uuid4()}@mail.example.test>"
    inbound_message_id = str(uuid4())

    with SessionLocal() as db:
        thread = CommunicationThread(
            subject="Water filtration question",
            status=CommunicationThreadStatus.open,
        )
        db.add(thread)
        db.flush()

        prior = CommunicationMessage(
            thread_id=thread.id,
            direction=CommunicationDirection.outbound,
            status=CommunicationMessageStatus.sent,
            provider="postmark",
            provider_message_id=str(uuid4()),
            internet_message_id=internet_message_id,
            sender_address="support@example.test",
            subject="Water filtration question",
        )
        db.add(prior)
        db.commit()
        thread_id = thread.id

    response = client.post(
        "/api/webhooks/postmark/inbound",
        json=inbound_payload(
            message_id=inbound_message_id,
            in_reply_to=internet_message_id,
        ),
        headers=basic_auth_header(),
    )

    assert response.status_code == 200
    assert response.json()["thread_id"] == str(thread_id)

    with SessionLocal() as db:
        thread = db.get(CommunicationThread, thread_id)
        assert thread is not None
        db.delete(thread)
        db.commit()


def test_inbound_mailbox_hash_can_target_existing_thread() -> None:
    inbound_message_id = str(uuid4())

    with SessionLocal() as db:
        thread = CommunicationThread(
            subject="Existing customer thread",
            status=CommunicationThreadStatus.closed,
        )
        db.add(thread)
        db.commit()
        thread_id = thread.id

    response = client.post(
        "/api/webhooks/postmark/inbound",
        json=inbound_payload(
            message_id=inbound_message_id,
            mailbox_hash=str(thread_id),
        ),
        headers=basic_auth_header(),
    )

    assert response.status_code == 200
    assert response.json()["thread_id"] == str(thread_id)

    with SessionLocal() as db:
        thread = db.get(CommunicationThread, thread_id)
        assert thread is not None
        assert thread.status == CommunicationThreadStatus.open
        db.delete(thread)
        db.commit()


def test_invalid_attachment_rolls_back_inbound_message() -> None:
    message_id = str(uuid4())
    payload = inbound_payload(message_id=message_id)
    payload["Attachments"] = [
        {
            "Name": "broken.txt",
            "Content": "not-valid-base64!",
            "ContentType": "text/plain",
            "ContentLength": 10,
        }
    ]

    response = client.post(
        "/api/webhooks/postmark/inbound",
        json=payload,
        headers=basic_auth_header(),
    )

    assert response.status_code == 422

    with SessionLocal() as db:
        message = db.scalar(
            select(CommunicationMessage).where(
                CommunicationMessage.provider == "postmark",
                CommunicationMessage.provider_message_id == message_id,
            )
        )
        assert message is None

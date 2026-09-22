from sqlalchemy import LargeBinary

from app.models.communications import (
    CommunicationAttachment,
    CommunicationEvent,
    CommunicationMessage,
    CommunicationRecipient,
    CommunicationThread,
)
from app.models.email import EmailDelivery


def column_names(model: type[object]) -> set[str]:
    return {
        column.name
        for column in model.__table__.columns  # type: ignore[attr-defined]
    }


def foreign_key_targets(model: type[object]) -> set[str]:
    return {
        foreign_key.target_fullname
        for foreign_key in model.__table__.foreign_keys  # type: ignore[attr-defined]
    }


def test_existing_delivery_ledger_remains_metadata_only() -> None:
    columns = column_names(EmailDelivery)

    assert "body" not in columns
    assert "body_text" not in columns
    assert "body_html" not in columns
    assert "raw_payload" not in columns


def test_archive_message_stores_durable_content() -> None:
    columns = column_names(CommunicationMessage)

    assert {
        "thread_id",
        "author_user_id",
        "email_delivery_id",
        "direction",
        "status",
        "provider",
        "provider_message_id",
        "internet_message_id",
        "in_reply_to",
        "sender_address",
        "subject",
        "body_text",
        "body_html",
        "content_redacted",
        "sent_at",
        "received_at",
    }.issubset(columns)

    assert "raw_payload" not in columns


def test_archive_models_link_threads_users_and_delivery_ledger() -> None:
    assert foreign_key_targets(
        CommunicationThread
    ) == {
        "users.id",
    }

    assert foreign_key_targets(
        CommunicationMessage
    ) == {
        "communication_threads.id",
        "users.id",
        "email_deliveries.id",
    }

    assert foreign_key_targets(
        CommunicationRecipient
    ) == {
        "communication_messages.id",
    }

    assert foreign_key_targets(
        CommunicationAttachment
    ) == {
        "communication_messages.id",
    }

    assert foreign_key_targets(
        CommunicationEvent
    ) == {
        "communication_messages.id",
    }


def test_attachment_content_is_archived_in_postgresql() -> None:
    content = CommunicationAttachment.__table__.c.content

    assert isinstance(
        content.type,
        LargeBinary,
    )
    assert content.nullable is False

    columns = column_names(
        CommunicationAttachment
    )

    assert {
        "filename",
        "content_type",
        "size_bytes",
        "sha256",
        "content",
    }.issubset(columns)


def test_provider_events_store_normalized_details_not_raw_payloads() -> None:
    columns = column_names(CommunicationEvent)

    assert {
        "provider",
        "event_type",
        "provider_event_id",
        "occurred_at",
        "details",
    }.issubset(columns)

    assert "raw_payload" not in columns

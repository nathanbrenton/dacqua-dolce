import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommunicationThreadStatus(StrEnum):
    open = "open"
    closed = "closed"


class CommunicationDirection(StrEnum):
    inbound = "inbound"
    outbound = "outbound"
    internal = "internal"


class CommunicationMessageStatus(StrEnum):
    draft = "draft"
    queued = "queued"
    sent = "sent"
    received = "received"
    failed = "failed"
    suppressed = "suppressed"


class CommunicationRecipientType(StrEnum):
    to = "to"
    cc = "cc"
    bcc = "bcc"
    reply_to = "reply_to"


class CommunicationThread(Base):
    __tablename__ = "communication_threads"
    __table_args__ = (
        Index(
            "ix_communication_threads_customer_user_id",
            "customer_user_id",
        ),
        Index(
            "ix_communication_threads_assigned_user_id",
            "assigned_user_id",
        ),
        Index(
            "ix_communication_threads_status_last_message",
            "status",
            "last_message_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    customer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    subject: Mapped[str | None] = mapped_column(
        String(300),
    )

    related_entity_type: Mapped[str | None] = mapped_column(
        String(80),
    )

    related_entity_id: Mapped[str | None] = mapped_column(
        String(120),
    )

    status: Mapped[CommunicationThreadStatus] = mapped_column(
        Enum(
            CommunicationThreadStatus,
            name="communication_thread_status",
        ),
        nullable=False,
        default=CommunicationThreadStatus.open,
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CommunicationMessage(Base):
    __tablename__ = "communication_messages"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_message_id",
            name=(
                "uq_communication_messages_"
                "provider_message_id"
            ),
        ),
        UniqueConstraint(
            "email_delivery_id",
            name=(
                "uq_communication_messages_"
                "email_delivery_id"
            ),
        ),
        Index(
            "ix_communication_messages_thread_created",
            "thread_id",
            "created_at",
        ),
        Index(
            "ix_communication_messages_direction_status",
            "direction",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "communication_threads.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    email_delivery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "email_deliveries.id",
            ondelete="SET NULL",
        ),
    )

    direction: Mapped[CommunicationDirection] = mapped_column(
        Enum(
            CommunicationDirection,
            name="communication_direction",
        ),
        nullable=False,
    )

    status: Mapped[CommunicationMessageStatus] = mapped_column(
        Enum(
            CommunicationMessageStatus,
            name="communication_message_status",
        ),
        nullable=False,
    )

    provider: Mapped[str | None] = mapped_column(
        String(40),
    )

    provider_message_id: Mapped[str | None] = mapped_column(
        String(300),
    )

    message_stream: Mapped[str | None] = mapped_column(
        String(80),
    )

    internet_message_id: Mapped[str | None] = mapped_column(
        String(500),
    )

    in_reply_to: Mapped[str | None] = mapped_column(
        String(500),
    )

    sender_address: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    sender_name: Mapped[str | None] = mapped_column(
        String(200),
    )

    subject: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    body_text: Mapped[str | None] = mapped_column(
        Text,
    )

    body_html: Mapped[str | None] = mapped_column(
        Text,
    )

    content_redacted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CommunicationRecipient(Base):
    __tablename__ = "communication_recipients"
    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "recipient_type",
            "address",
            name=(
                "uq_communication_recipients_"
                "message_type_address"
            ),
        ),
        Index(
            "ix_communication_recipients_message_type",
            "message_id",
            "recipient_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "communication_messages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    recipient_type: Mapped[CommunicationRecipientType] = mapped_column(
        Enum(
            CommunicationRecipientType,
            name="communication_recipient_type",
        ),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(200),
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )


class CommunicationAttachment(Base):
    __tablename__ = "communication_attachments"
    __table_args__ = (
        Index(
            "ix_communication_attachments_message_id",
            "message_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "communication_messages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider_attachment_id: Mapped[str | None] = mapped_column(
        String(300),
    )

    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content_id: Mapped[str | None] = mapped_column(
        String(500),
    )

    content_disposition: Mapped[str | None] = mapped_column(
        String(40),
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    content: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CommunicationEvent(Base):
    __tablename__ = "communication_events"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_event_id",
            name=(
                "uq_communication_events_"
                "provider_event_id"
            ),
        ),
        Index(
            "ix_communication_events_message_occurred",
            "message_id",
            "occurred_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "communication_messages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    provider_event_id: Mapped[str | None] = mapped_column(
        String(300),
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    details: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

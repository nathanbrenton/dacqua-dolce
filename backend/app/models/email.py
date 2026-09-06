import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    Enum,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class EmailDeliveryStatus(StrEnum):
    pending = "pending"
    sent = "sent"
    suppressed = "suppressed"
    failed = "failed"


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    related_entity_type: Mapped[str | None] = mapped_column(
        String(80),
    )

    related_entity_id: Mapped[str | None] = mapped_column(
        String(120),
    )

    provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    sender: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    recipient: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    status: Mapped[EmailDeliveryStatus] = mapped_column(
        Enum(
            EmailDeliveryStatus,
            name="email_delivery_status",
        ),
        nullable=False,
        default=(EmailDeliveryStatus.pending),
    )

    provider_reference: Mapped[str | None] = mapped_column(
        String(300),
    )

    error_summary: Mapped[str | None] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

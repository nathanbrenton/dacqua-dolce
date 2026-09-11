import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuoteRequestStatus(StrEnum):
    new = "new"
    contacted = "contacted"
    quoted = "quoted"
    closed = "closed"


class QuoteRequest(Base):
    __tablename__ = "quote_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="SET NULL",
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
    )

    message: Mapped[str | None] = mapped_column(
        Text,
    )

    internal_notes: Mapped[str | None] = mapped_column(
        Text,
    )

    status: Mapped[QuoteRequestStatus] = mapped_column(
        Enum(
            QuoteRequestStatus,
            name="quote_request_status",
        ),
        nullable=False,
        default=QuoteRequestStatus.new,
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

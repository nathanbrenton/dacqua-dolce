import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
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


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="Home",
    )

    line1: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    line2: Mapped[str | None] = mapped_column(
        String(200),
    )

    city: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    region_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    postal_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US",
    )

    is_default_shipping: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_default_billing: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.catalog import ReminderPreferenceKind


class MaintenanceReminderStatus(StrEnum):
    sent = "sent"
    failed = "failed"
    suppressed = "suppressed"


class MaintenanceReminder(Base):
    __tablename__ = "maintenance_reminders"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id",
            "related_product_id",
            "reminder_kind",
            "due_on",
            name="uq_maintenance_reminder_business_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    related_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reminder_kind: Mapped[ReminderPreferenceKind] = mapped_column(
        Enum(
            ReminderPreferenceKind,
            name="reminder_preference_kind",
            create_type=False,
        ),
        nullable=False,
    )
    due_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    recipient: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )
    status: Mapped[MaintenanceReminderStatus] = mapped_column(
        Enum(
            MaintenanceReminderStatus,
            name="maintenance_reminder_status",
        ),
        nullable=False,
    )
    email_delivery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_deliveries.id", ondelete="SET NULL"),
    )
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LaunchDependencyEvidence(Base):
    """Internal-only tracking record for external launch dependency evidence.

    This table never opens commerce and never replaces service-level readiness
    checks. It records staff workflow/evidence references only.
    """

    __tablename__ = "launch_dependency_evidence"
    __table_args__ = (
        CheckConstraint(
            "dependency_key IN ("
            "'tax', "
            "'payment_checkout', "
            "'legal_review', "
            "'shipping_insurance', "
            "'support_phone', "
            "'installer_program'"
            ")",
            name="launch_dependency_evidence_key_supported",
        ),
        CheckConstraint(
            "tracking_status IN ("
            "'action_required', "
            "'in_progress', "
            "'evidence_received', "
            "'verified', "
            "'blocked'"
            ")",
            name="launch_dependency_evidence_status_supported",
        ),
        Index(
            "ix_launch_dependency_evidence_status_updated",
            "tracking_status",
            "updated_at",
        ),
    )

    dependency_key: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    tracking_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="action_required",
    )
    source_reference: Mapped[str | None] = mapped_column(Text)
    evidence_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    internal_notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    updated_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
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

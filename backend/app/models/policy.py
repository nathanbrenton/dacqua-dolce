from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PolicyKind(StrEnum):
    privacy = "privacy"
    terms = "terms"
    shipping = "shipping"
    cancellation = "cancellation"
    refund = "refund"
    warranty = "warranty"
    installation = "installation"


class PolicyDocumentStatus(StrEnum):
    draft = "draft"
    approved = "approved"
    retired = "retired"


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    __table_args__ = (
        UniqueConstraint(
            "kind",
            "version",
            name="uq_policy_documents_kind_version",
        ),
        Index(
            "uq_policy_documents_one_approved_per_kind",
            "kind",
            unique=True,
            postgresql_where=text("status = 'approved'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    kind: Mapped[PolicyKind] = mapped_column(
        Enum(
            PolicyKind,
            name="policy_kind",
        ),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[PolicyDocumentStatus] = mapped_column(
        Enum(
            PolicyDocumentStatus,
            name="policy_document_status",
        ),
        nullable=False,
        default=PolicyDocumentStatus.draft,
    )

    effective_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
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


class FormalQuotePolicySnapshot(Base):
    __tablename__ = "formal_quote_policy_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "formal_quote_id",
            "kind",
            name="uq_formal_quote_policy_snapshots_quote_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    formal_quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "formal_quotes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    policy_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "policy_documents.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    kind: Mapped[PolicyKind] = mapped_column(
        Enum(
            PolicyKind,
            name="policy_kind",
            create_type=False,
        ),
        nullable=False,
    )

    version_snapshot: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    title_snapshot: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    body_snapshot: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    effective_at_snapshot: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    formal_quote = relationship(
        "FormalQuote",
        back_populates="policy_snapshots",
    )

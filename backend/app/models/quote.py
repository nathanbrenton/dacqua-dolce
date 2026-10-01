from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuoteRequestStatus(StrEnum):
    new = "new"
    contacted = "contacted"
    quoted = "quoted"
    closed = "closed"


class FormalQuoteStatus(StrEnum):
    draft = "draft"
    presented = "presented"
    approved = "approved"
    superseded = "superseded"


class CommercialChargeKind(StrEnum):
    shipping = "shipping"
    tax = "tax"
    installation = "installation"
    discount = "discount"
    other_charge = "other_charge"
    other_credit = "other_credit"


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

    recommendation_context: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
    )

    recommendation_decision: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
    )

    recommendation_policy_version: Mapped[str | None] = mapped_column(
        String(40),
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

    formal_quotes: Mapped[list[FormalQuote]] = relationship(
        back_populates="quote_request",
        cascade="all, delete-orphan",
        order_by="FormalQuote.revision_number",
    )


class FormalQuote(Base):
    __tablename__ = "formal_quotes"
    __table_args__ = (
        UniqueConstraint(
            "quote_request_id",
            "revision_number",
            name="uq_formal_quotes_request_revision",
        ),
        CheckConstraint(
            "revision_number > 0",
            name="formal_quotes_revision_positive",
        ),
        CheckConstraint(
            "subtotal_amount_minor >= 0",
            name="formal_quotes_subtotal_nonnegative",
        ),
        CheckConstraint(
            "total_amount_minor >= 0",
            name="formal_quotes_total_nonnegative",
        ),
        CheckConstraint(
            "total_amount_minor = subtotal_amount_minor + charges_amount_minor",
            name="formal_quotes_total_matches_components",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    quote_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "quote_requests.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    revision_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[FormalQuoteStatus] = mapped_column(
        Enum(
            FormalQuoteStatus,
            name="formal_quote_status",
        ),
        nullable=False,
        default=FormalQuoteStatus.draft,
    )

    customer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    authored_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    subtotal_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    charges_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    total_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    delivery_address_snapshot: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
    )

    billing_address_snapshot: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
    )

    customer_note: Mapped[str | None] = mapped_column(
        Text,
    )

    presented_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    expires_at: Mapped[datetime | None] = mapped_column(
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

    quote_request: Mapped[QuoteRequest] = relationship(
        back_populates="formal_quotes",
    )

    items: Mapped[list[FormalQuoteItem]] = relationship(
        back_populates="formal_quote",
        cascade="all, delete-orphan",
        order_by="FormalQuoteItem.sort_order",
    )

    charges: Mapped[list[FormalQuoteCharge]] = relationship(
        back_populates="formal_quote",
        cascade="all, delete-orphan",
        order_by="FormalQuoteCharge.sort_order",
    )

    policy_snapshots = relationship(
        "FormalQuotePolicySnapshot",
        back_populates="formal_quote",
        cascade="all, delete-orphan",
        order_by="FormalQuotePolicySnapshot.sort_order",
    )


class FormalQuoteCharge(Base):
    __tablename__ = "formal_quote_charges"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('shipping', 'tax', 'installation', 'discount', "
            "'other_charge', 'other_credit')",
            name="formal_quote_charges_kind_valid",
        ),
        CheckConstraint(
            "((kind IN ('shipping', 'tax', 'installation', 'other_charge') "
            "AND amount_minor > 0) OR "
            "(kind IN ('discount', 'other_credit') AND amount_minor < 0))",
            name="formal_quote_charges_amount_sign_valid",
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

    kind: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
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

    formal_quote: Mapped[FormalQuote] = relationship(
        back_populates="charges",
    )


class FormalQuoteItem(Base):
    __tablename__ = "formal_quote_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="formal_quote_items_quantity_positive",
        ),
        CheckConstraint(
            "unit_amount_minor >= 0",
            name="formal_quote_items_unit_amount_nonnegative",
        ),
        CheckConstraint(
            "line_total_minor >= 0",
            name="formal_quote_items_line_total_nonnegative",
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

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="SET NULL",
        ),
    )

    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "product_variants.id",
            ondelete="SET NULL",
        ),
    )

    sku_snapshot: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name_snapshot: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    line_total_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    pricing_policy_mode_snapshot: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    estimated_lead_time_snapshot: Mapped[str | None] = mapped_column(
        String(120),
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

    formal_quote: Mapped[FormalQuote] = relationship(
        back_populates="items",
    )

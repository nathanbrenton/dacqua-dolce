from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductTaxClassification(Base):
    __tablename__ = "product_tax_classifications"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "provider",
            name="uq_product_tax_classifications_product_provider",
        ),
        Index(
            "ix_product_tax_classifications_provider_active",
            "provider",
            "active",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    tax_code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    source_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    verified_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    product = relationship(
        "Product",
        back_populates="tax_classifications",
    )


class TaxCalculation(Base):
    __tablename__ = "tax_calculations"
    __table_args__ = (
        CheckConstraint(
            "((formal_quote_id IS NOT NULL AND order_id IS NULL) OR "
            "(formal_quote_id IS NULL AND order_id IS NOT NULL))",
            name="tax_calculations_single_context",
        ),
        CheckConstraint(
            "line_items_amount_minor >= 0",
            name="tax_calculations_line_items_nonnegative",
        ),
        CheckConstraint(
            "shipping_amount_minor >= 0",
            name="tax_calculations_shipping_nonnegative",
        ),
        CheckConstraint(
            "tax_amount_minor >= 0",
            name="tax_calculations_tax_nonnegative",
        ),
        CheckConstraint(
            "amount_total_minor >= 0",
            name="tax_calculations_total_nonnegative",
        ),
        UniqueConstraint(
            "provider",
            "provider_calculation_id",
            name="uq_tax_calculations_provider_calculation",
        ),
        Index(
            "ix_tax_calculations_formal_quote_created",
            "formal_quote_id",
            "created_at",
        ),
        Index(
            "ix_tax_calculations_order_created",
            "order_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    formal_quote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("formal_quotes.id", ondelete="CASCADE"),
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
    )
    provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    provider_calculation_id: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    line_items_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    shipping_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    tax_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    amount_total_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    livemode: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    request_summary: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
    response_summary: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
    superseded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    committed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TaxTransaction(Base):
    __tablename__ = "tax_transactions"
    __table_args__ = (
        CheckConstraint(
            "tax_amount_minor >= 0",
            name="tax_transactions_tax_nonnegative",
        ),
        CheckConstraint(
            "amount_total_minor >= 0",
            name="tax_transactions_total_nonnegative",
        ),
        UniqueConstraint(
            "order_id",
            name="uq_tax_transactions_order",
        ),
        UniqueConstraint(
            "calculation_id",
            name="uq_tax_transactions_calculation",
        ),
        UniqueConstraint(
            "provider",
            "provider_transaction_id",
            name="uq_tax_transactions_provider_transaction",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calculation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tax_calculations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    provider_transaction_id: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    provider_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    tax_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    amount_total_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    livemode: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    response_summary: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

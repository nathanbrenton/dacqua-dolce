import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.catalog import PricingPolicyMode


class CartStatus(StrEnum):
    active = "active"
    converted = "converted"
    abandoned = "abandoned"


class OrderStatus(StrEnum):
    draft = "draft"
    awaiting_payment = "awaiting_payment"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    refunded = "refunded"


class PaymentReferenceStatus(StrEnum):
    created = "created"
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class Cart(Base):
    __tablename__ = "carts"

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

    status: Mapped[CartStatus] = mapped_column(
        Enum(
            CartStatus,
            name="cart_status",
        ),
        nullable=False,
        default=CartStatus.active,
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


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="quantity_positive",
        ),
        CheckConstraint(
            "unit_amount_minor >= 0",
            name="unit_amount_minor_nonnegative",
        ),
        Index(
            "ix_cart_items_reservation_scope",
            "product_id",
            "variant_id",
            "reservation_expires_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "carts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "product_variants.id",
            ondelete="RESTRICT",
        ),
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    unit_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    # pricing_policy_mode is created by the catalog migration.
    # Reuse that PostgreSQL enum type; do not emit CREATE TYPE again.
    pricing_policy_mode: Mapped[PricingPolicyMode] = mapped_column(
        PGEnum(
            PricingPolicyMode,
            name="pricing_policy_mode",
            create_type=False,
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

    reservation_expires_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
    )


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "total_amount_minor >= 0",
            name="total_amount_minor_nonnegative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
        ),
        nullable=False,
        default=OrderStatus.draft,
    )

    total_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
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


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="quantity_positive",
        ),
        CheckConstraint(
            "unit_amount_minor >= 0",
            name="unit_amount_minor_nonnegative",
        ),
        CheckConstraint(
            "line_total_minor >= 0",
            name="line_total_minor_nonnegative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "orders.id",
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
        String(200),
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class PaymentProviderReference(Base):
    """Provider-issued payment references and minimal safe display metadata.

    This table intentionally does not contain PAN, CVV/CVC, expiration dates,
    track data, PIN data, authentication data, or raw provider payloads.
    """

    __tablename__ = "payment_provider_references"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    provider_checkout_id: Mapped[str | None] = mapped_column(
        String(300),
    )

    provider_payment_id: Mapped[str | None] = mapped_column(
        String(300),
    )

    provider_customer_id: Mapped[str | None] = mapped_column(
        String(300),
    )

    payment_method_type: Mapped[str | None] = mapped_column(
        String(80),
    )

    payment_method_brand: Mapped[str | None] = mapped_column(
        String(80),
    )

    payment_method_last4: Mapped[str | None] = mapped_column(
        String(4),
    )

    status: Mapped[PaymentReferenceStatus] = mapped_column(
        Enum(
            PaymentReferenceStatus,
            name="payment_reference_status",
        ),
        nullable=False,
        default=PaymentReferenceStatus.created,
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

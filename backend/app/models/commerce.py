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
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
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


class FulfillmentStatus(StrEnum):
    not_started = "not_started"
    supplier_ordered = "supplier_ordered"
    received_ready = "received_ready"
    shipped = "shipped"
    delivered = "delivered"


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
        CheckConstraint(
            "subtotal_amount_minor >= 0",
            name="orders_subtotal_nonnegative",
        ),
        CheckConstraint(
            "total_amount_minor = subtotal_amount_minor + charges_amount_minor",
            name="orders_total_matches_components",
        ),
        UniqueConstraint(
            "formal_quote_id",
            name="uq_orders_formal_quote_id",
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

    formal_quote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "formal_quotes.id",
            ondelete="RESTRICT",
        ),
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
        ),
        nullable=False,
        default=OrderStatus.draft,
    )

    fulfillment_status: Mapped[FulfillmentStatus] = mapped_column(
        Enum(
            FulfillmentStatus,
            name="fulfillment_status",
        ),
        nullable=False,
        default=FulfillmentStatus.not_started,
    )

    supplier_order_reference: Mapped[str | None] = mapped_column(
        String(160),
    )

    supplier_ordered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    received_ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    fulfillment_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    subtotal_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    charges_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    total_amount_minor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    delivery_address_snapshot: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
    )

    billing_address_snapshot: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
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


class OrderCancellationRequest(Base):
    __tablename__ = "order_cancellation_requests"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            name="uq_order_cancellation_requests_order_id",
        ),
        CheckConstraint(
            "eligibility_mode IN ('unrestricted', 'manual_review')",
            name="cancellation_mode_valid",
        ),
        CheckConstraint(
            "status IN ('requested', 'approved', 'declined', 'completed')",
            name="cancellation_status_valid",
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

    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    eligibility_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
    )

    supplier_ordered_at_snapshot: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    review_note: Mapped[str | None] = mapped_column(
        Text,
    )

    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
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

    estimated_lead_time_snapshot: Mapped[str | None] = mapped_column(
        String(120),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class OrderCharge(Base):
    __tablename__ = "order_charges"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('shipping', 'tax', 'installation', 'discount', "
            "'other_charge', 'other_credit')",
            name="order_charges_kind_valid",
        ),
        CheckConstraint(
            "((kind IN ('shipping', 'tax', 'installation', 'other_charge') "
            "AND amount_minor > 0) OR "
            "(kind IN ('discount', 'other_credit') AND amount_minor < 0))",
            name="order_charges_amount_sign_valid",
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


class OrderShipment(Base):
    __tablename__ = "order_shipments"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            name="uq_order_shipments_order_id",
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

    carrier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tracking_number: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    tracking_url: Mapped[str | None] = mapped_column(
        String(2048),
    )

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
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


class PaymentProviderReference(Base):
    """Provider-issued payment references and minimal safe display metadata.

    This table intentionally does not contain PAN, CVV/CVC, expiration dates,
    track data, PIN data, authentication data, or raw provider payloads.
    """

    __tablename__ = "payment_provider_references"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_checkout_id",
            name="uq_payment_provider_references_provider_checkout",
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


class PaymentProviderEvent(Base):
    """Normalized, verified provider event with no raw payment payload.

    A gateway-specific adapter must authenticate the inbound webhook and
    translate it to this narrow safe record before the application can use it.
    Raw provider payloads and cardholder data are intentionally not stored.
    """

    __tablename__ = "payment_provider_events"
    __table_args__ = (
        CheckConstraint(
            "amount_minor IS NULL OR amount_minor >= 0",
            name="amount_minor_nonnegative",
        ),
        UniqueConstraint(
            "provider",
            "provider_event_id",
            name="uq_payment_provider_events_provider_event",
        ),
        Index(
            "ix_payment_provider_events_reference_created",
            "payment_reference_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    payment_reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "payment_provider_references.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    provider_event_id: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    status: Mapped[PaymentReferenceStatus] = mapped_column(
        PGEnum(
            PaymentReferenceStatus,
            name="payment_reference_status",
            create_type=False,
        ),
        nullable=False,
    )

    amount_minor: Mapped[int | None] = mapped_column(
        BigInteger,
    )

    currency: Mapped[str | None] = mapped_column(
        String(3),
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

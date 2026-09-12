from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PricingPolicyMode(StrEnum):
    PUBLIC = "PUBLIC"
    MAP_LIMITED = "MAP_LIMITED"
    CART_ONLY = "CART_ONLY"
    PRIVATE_QUOTE = "PRIVATE_QUOTE"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    NO_ONLINE_PRICE = "NO_ONLINE_PRICE"
    NO_ONLINE_SALE = "NO_ONLINE_SALE"


class InventoryStatus(StrEnum):
    in_stock = "in_stock"
    low_stock = "low_stock"
    backordered = "backordered"
    unavailable = "unavailable"
    not_tracked = "not_tracked"


class ProductDocumentType(StrEnum):
    specification = "specification"
    installation = "installation"
    care_guide = "care_guide"
    warranty = "warranty"
    certification = "certification"
    other = "other"


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        unique=True,
    )
    slug: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        unique=True,
    )
    public_summary: Mapped[str | None] = mapped_column(Text)
    internal_policy_notes: Mapped[str | None] = mapped_column(Text)
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

    products: Mapped[list[Product]] = relationship(back_populates="manufacturer")


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
    )
    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    products: Mapped[list[Product]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint(
            "sku",
            name="uq_products_sku",
        ),
        UniqueConstraint(
            "slug",
            name="uq_products_slug",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    manufacturer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "manufacturers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "product_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    product_family: Mapped[str | None] = mapped_column(String(120))
    online_sale_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    public_path: Mapped[str] = mapped_column(
        String(300),
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

    manufacturer: Mapped[Manufacturer] = relationship(back_populates="products")
    category: Mapped[ProductCategory] = relationship(back_populates="products")
    variants: Mapped[list[ProductVariant]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.display_name",
    )
    prices: Mapped[list[ProductPrice]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    inventory: Mapped[list[ProductInventory]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )
    documents: Mapped[list[ProductDocument]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    specifications: Mapped[list[ProductSpecification]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSpecification.sort_order",
    )
    approved_claims: Mapped[list[ApprovedProductClaim]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    jurisdiction_rules: Mapped[list[JurisdictionEligibility]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint(
            "sku",
            name="uq_product_variants_sku",
        ),
        UniqueConstraint(
            "product_id",
            "display_name",
            name="uq_product_variants_product_display_name",
        ),
        CheckConstraint(
            "jsonb_typeof(option_values) = 'object'",
            name="option_values_object",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    option_values: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
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

    product: Mapped[Product] = relationship(back_populates="variants")
    prices: Mapped[list[ProductPrice]] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
    )
    inventory: Mapped[list[ProductInventory]] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
    )


class ProductPrice(Base):
    __tablename__ = "product_prices"
    __table_args__ = (
        CheckConstraint(
            "amount_minor IS NULL OR amount_minor >= 0",
            name="amount_minor_nonnegative",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_until > effective_from",
            name="effective_window_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "product_variants.id",
            ondelete="CASCADE",
        ),
    )
    pricing_policy_mode: Mapped[PricingPolicyMode] = mapped_column(
        Enum(
            PricingPolicyMode,
            name="pricing_policy_mode",
        ),
        nullable=False,
    )
    amount_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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

    product: Mapped[Product] = relationship(back_populates="prices")
    variant: Mapped[ProductVariant | None] = relationship(back_populates="prices")


class ProductInventory(Base):
    __tablename__ = "product_inventory"
    __table_args__ = (
        CheckConstraint(
            "quantity_on_hand >= 0",
            name="quantity_on_hand_nonnegative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "product_variants.id",
            ondelete="CASCADE",
        ),
    )
    inventory_status: Mapped[InventoryStatus] = mapped_column(
        Enum(
            InventoryStatus,
            name="inventory_status",
        ),
        nullable=False,
        default=InventoryStatus.not_tracked,
    )
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    product: Mapped[Product] = relationship(back_populates="inventory")
    variant: Mapped[ProductVariant | None] = relationship(back_populates="inventory")


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    alt_text: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    product: Mapped[Product] = relationship(back_populates="images")


class ProductDocument(Base):
    __tablename__ = "product_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    document_type: Mapped[ProductDocumentType] = mapped_column(
        Enum(
            ProductDocumentType,
            name="product_document_type",
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="1",
    )
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    product: Mapped[Product] = relationship(back_populates="documents")


class ProductSpecification(Base):
    __tablename__ = "product_specifications"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "spec_key",
            name="uq_product_specifications_product_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    spec_key: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    value_text: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    unit: Mapped[str | None] = mapped_column(
        String(60),
    )
    source_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
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

    product: Mapped[Product] = relationship(
        back_populates="specifications",
    )


class ApprovedProductClaim(Base):
    __tablename__ = "approved_product_claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    claim_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    approved_by: Mapped[str | None] = mapped_column(String(160))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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

    product: Mapped[Product] = relationship(back_populates="approved_claims")


class JurisdictionEligibility(Base):
    __tablename__ = "jurisdiction_eligibility"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "country_code",
            "region_code",
            name="uq_jurisdiction_eligibility_product_region",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US",
    )
    region_code: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
    sale_eligible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    return_eligible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    service_eligible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    operator_notes: Mapped[str | None] = mapped_column(Text)
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

    product: Mapped[Product] = relationship(back_populates="jurisdiction_rules")

from pydantic import BaseModel, Field, field_validator

from app.core.email import normalize_email_address


class CatalogPricingRead(BaseModel):
    mode: str
    amount_minor: int | None = None
    currency: str | None = None
    display_price: bool
    can_add_to_cart: bool
    can_checkout_online: bool
    action: str
    action_label: str


class CatalogAvailabilityRead(BaseModel):
    status: str
    available: bool | None
    action: str
    action_label: str
    lifecycle_status: str
    expected_available_on: str | None = None
    estimated_lead_time: str | None = None
    can_notify_when_in_stock: bool = False
    can_inquire: bool = True


class StockNotificationRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return normalize_email_address(value)


class StockNotificationRead(BaseModel):
    status: str
    message: str


class CatalogImageRead(BaseModel):
    path: str
    alt_text: str


class CatalogSpecificationRead(BaseModel):
    spec_key: str
    label: str
    value_text: str
    unit: str | None = None


class CatalogManufacturerClaimRead(BaseModel):
    claim_text: str
    source_reference: str
    provenance_label: str = "Manufacturer-stated"


class CatalogOptionRead(BaseModel):
    id: str
    relationship_type: str
    name: str
    slug: str
    product_family: str | None
    system_type: str | None
    public_path: str


class CatalogVariantRead(BaseModel):
    id: str
    display_name: str
    sku: str
    option_values: dict[str, str]


class CatalogDocumentRead(BaseModel):
    title: str
    document_type: str
    path: str
    content_type: str
    version: str
    verified_at: str | None = None


class CatalogProductRead(BaseModel):
    id: str
    name: str
    slug: str
    sku: str
    description: str
    product_family: str | None
    system_type: str | None
    category: str
    public_path: str
    primary_image: CatalogImageRead | None
    pricing: CatalogPricingRead
    availability: CatalogAvailabilityRead


class CatalogProductDetailRead(CatalogProductRead):
    images: list[CatalogImageRead] = Field(default_factory=list)
    variants: list[CatalogVariantRead] = Field(default_factory=list)
    options_accessories: list[CatalogOptionRead] = Field(default_factory=list)
    documents: list[CatalogDocumentRead] = Field(default_factory=list)
    specifications: list[CatalogSpecificationRead] = Field(
        default_factory=list,
    )
    manufacturer_claims: list[CatalogManufacturerClaimRead] = Field(
        default_factory=list,
    )


class CatalogProductListResponse(BaseModel):
    products: list[CatalogProductRead] = Field(default_factory=list)

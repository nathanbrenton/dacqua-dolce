from pydantic import BaseModel, Field


class CatalogPricingRead(BaseModel):
    mode: str
    amount_minor: int | None = None
    currency: str | None = None
    display_price: bool
    can_add_to_cart: bool
    can_checkout_online: bool
    action: str
    action_label: str


class CatalogImageRead(BaseModel):
    path: str
    alt_text: str


class CatalogSpecificationRead(BaseModel):
    spec_key: str
    label: str
    value_text: str
    unit: str | None = None


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


class CatalogProductRead(BaseModel):
    id: str
    name: str
    slug: str
    sku: str
    description: str
    product_family: str | None
    manufacturer: str
    category: str
    public_path: str
    primary_image: CatalogImageRead | None
    pricing: CatalogPricingRead


class CatalogProductDetailRead(CatalogProductRead):
    images: list[CatalogImageRead] = Field(default_factory=list)
    variants: list[CatalogVariantRead] = Field(default_factory=list)
    documents: list[CatalogDocumentRead] = Field(default_factory=list)
    specifications: list[CatalogSpecificationRead] = Field(
        default_factory=list,
    )


class CatalogProductListResponse(BaseModel):
    products: list[CatalogProductRead] = Field(default_factory=list)

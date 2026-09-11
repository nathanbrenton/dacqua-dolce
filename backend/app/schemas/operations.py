from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from app.models.catalog import (
    InventoryStatus,
    PricingPolicyMode,
)
from app.models.quote import (
    QuoteRequestStatus,
)


class OperationsSummaryRead(BaseModel):
    new_quotes: int
    open_quotes: int
    active_products: int
    failed_email_deliveries: int


class OperationsQuoteRead(BaseModel):
    id: str
    product_id: str | None
    product_name: str | None
    name: str
    email: str
    phone: str | None
    message: str | None
    internal_notes: str | None
    status: str
    created_at: str


class OperationsCustomerAddressRead(BaseModel):
    id: str
    label: str
    line1: str
    line2: str | None
    city: str
    region_code: str
    postal_code: str
    country_code: str
    is_default_shipping: bool
    is_default_billing: bool


class OperationsCustomerRead(BaseModel):
    id: str
    email: str
    status: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    addresses: list[OperationsCustomerAddressRead] = Field(
        default_factory=list,
    )
    created_at: str


class QuoteStatusUpdate(BaseModel):
    status: QuoteRequestStatus


class QuoteNotesUpdate(BaseModel):
    internal_notes: str | None = Field(
        default=None,
        max_length=8000,
    )

    @field_validator("internal_notes")
    @classmethod
    def clean_internal_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


class OperationsPricingRead(BaseModel):
    mode: str
    amount_minor: int | None
    currency: str | None
    effective_from: str | None


class OperationsInventoryRead(BaseModel):
    status: str
    quantity_on_hand: int
    quantity_reserved: int


class OperationsProductRead(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    manufacturer: str
    active: bool
    pricing: OperationsPricingRead
    inventory: OperationsInventoryRead


class PricingUpdateRequest(BaseModel):
    mode: PricingPolicyMode
    amount_minor: int | None = Field(
        default=None,
        ge=0,
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_amount_for_mode(
        self,
    ) -> "PricingUpdateRequest":
        amount_required_modes = {
            PricingPolicyMode.PUBLIC,
            PricingPolicyMode.MAP_LIMITED,
            PricingPolicyMode.CART_ONLY,
            PricingPolicyMode.LOGIN_REQUIRED,
        }

        amount_forbidden_modes = {
            PricingPolicyMode.PRIVATE_QUOTE,
            PricingPolicyMode.NO_ONLINE_PRICE,
            PricingPolicyMode.NO_ONLINE_SALE,
        }

        if self.mode in amount_required_modes and self.amount_minor is None:
            raise ValueError("This pricing policy requires an authoritative amount.")

        if self.mode in amount_forbidden_modes and self.amount_minor is not None:
            raise ValueError("This pricing policy must not store an online price amount.")

        return self


class InventoryUpdateRequest(BaseModel):
    status: InventoryStatus
    quantity_on_hand: int = Field(
        ge=0,
        le=1_000_000,
    )
    quantity_reserved: int = Field(
        ge=0,
        le=1_000_000,
    )

    @model_validator(mode="after")
    def reserved_not_above_on_hand(
        self,
    ) -> "InventoryUpdateRequest":
        if self.quantity_reserved > self.quantity_on_hand:
            raise ValueError("Reserved quantity cannot exceed quantity on hand.")

        return self

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from app.core.phone import (
    normalize_us_phone,
)
from app.schemas.commercial import (
    CommercialAddressSnapshot,
    CommercialChargeRead,
)
from app.schemas.policies import FormalQuotePolicySnapshotRead


class AddressCreate(BaseModel):
    label: str = Field(
        default="Home",
        min_length=1,
        max_length=80,
    )
    line1: str = Field(
        min_length=1,
        max_length=200,
    )
    line2: str | None = Field(
        default=None,
        max_length=200,
    )
    city: str = Field(
        min_length=1,
        max_length=120,
    )
    region_code: str = Field(
        min_length=1,
        max_length=32,
    )
    postal_code: str = Field(
        min_length=1,
        max_length=32,
    )
    country_code: str = Field(
        default="US",
        min_length=2,
        max_length=2,
    )
    is_default_shipping: bool = False
    is_default_billing: bool = False

    @field_validator(
        "label",
        "line1",
        "line2",
        "city",
        "region_code",
        "postal_code",
        "country_code",
    )
    @classmethod
    def clean_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


class AddressRead(AddressCreate):
    id: str


class CustomerProfileUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        max_length=100,
    )
    phone: str | None = Field(
        default=None,
        max_length=50,
    )

    @field_validator(
        "first_name",
        "last_name",
    )
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @field_validator(
        "phone",
        mode="before",
    )
    @classmethod
    def normalize_phone(
        cls,
        value: object,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Phone number must be text."
            )

        return normalize_us_phone(value)


class CustomerProfileRead(BaseModel):
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    addresses: list[AddressRead] = Field(
        default_factory=list
    )


class CommunicationPreferencesUpdate(BaseModel):
    filter_replacement_reminders: bool = False
    softener_check_reminders: bool = False
    uv_service_reminders: bool = False
    annual_system_check_reminders: bool = False
    product_specific_reminders: bool = False
    post_purchase_followup: bool = False
    post_installation_followup: bool = False


class CommunicationPreferencesRead(CommunicationPreferencesUpdate):
    pass


class CustomerRequestRead(BaseModel):
    id: str
    status: str
    product_name: str | None
    created_at: str
    recommendation_title: str | None = None
    human_review: bool = False
    requires_third_party_lab: bool = False


class CustomerFormalQuoteItemRead(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_amount_minor: int
    line_total_minor: int
    currency: str
    estimated_lead_time: str | None = None


class CustomerFormalQuoteRead(BaseModel):
    id: str
    request_id: str
    revision_number: int
    status: str
    currency: str
    subtotal_amount_minor: int
    charges_amount_minor: int
    total_amount_minor: int
    delivery_address: CommercialAddressSnapshot | None
    billing_address: CommercialAddressSnapshot | None
    charges: list[CommercialChargeRead] = Field(default_factory=list)
    policy_snapshots: list[FormalQuotePolicySnapshotRead] = Field(default_factory=list)
    customer_note: str | None
    presented_at: str | None
    approved_at: str | None
    created_at: str
    items: list[CustomerFormalQuoteItemRead] = Field(default_factory=list)


class CustomerEquipmentDocumentRead(BaseModel):
    title: str
    document_type: str
    path: str
    content_type: str
    version: str


class CustomerConsumableRead(BaseModel):
    product_id: str
    name: str
    sku: str
    public_path: str
    replacement_interval_days: int | None = None
    next_replacement_due_on: str | None = None
    calendar_path: str | None = None
    online_reorder_available: bool = False


class CustomerEquipmentRead(BaseModel):
    id: str
    product_id: str | None
    product_name: str
    product_family: str | None = None
    system_type: str | None = None
    sku: str
    variant_name: str | None = None
    serial_number: str | None = None
    location_label: str | None = None
    installed_on: str | None = None
    last_service_on: str | None = None
    next_service_due_on: str | None = None
    service_calendar_path: str | None = None
    consumables: list[CustomerConsumableRead] = Field(default_factory=list)
    documents: list[CustomerEquipmentDocumentRead] = Field(default_factory=list)

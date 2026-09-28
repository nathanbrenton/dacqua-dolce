from datetime import date
import uuid
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.catalog import (
    InventoryStatus,
    PricingPolicyMode,
    ProductRelationshipType,
)
from app.models.communications import (
    CommunicationThreadStatus,
)
from app.models.quote import (
    QuoteRequestStatus,
)


class OperationsSummaryRead(BaseModel):
    new_quotes: int
    open_quotes: int
    recommendation_human_review: int
    recommendation_lab_testing: int
    active_products: int
    failed_email_deliveries: int


class OperationsAuditEventRead(BaseModel):
    id: str
    actor_user_id: str | None
    actor_email: str | None
    action: str
    entity_type: str
    entity_id: str | None
    environment: str
    created_at: str


class OperationsCommunicationRead(BaseModel):
    id: str
    category: str
    related_entity_type: str | None
    related_entity_id: str | None
    sender: str
    recipient: str
    subject: str
    status: str
    created_at: str
    sent_at: str | None


class OperationsCommunicationRecipientRead(BaseModel):
    recipient_type: str
    address: str
    display_name: str | None


class OperationsCommunicationAttachmentRead(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str


class OperationsCommunicationMessageRead(BaseModel):
    id: str
    direction: str
    status: str
    author_user_id: str | None
    sender_address: str
    sender_name: str | None
    subject: str
    body_text: str | None
    content_redacted: bool
    sent_at: str | None
    received_at: str | None
    created_at: str
    recipients: list[OperationsCommunicationRecipientRead] = Field(
        default_factory=list,
    )
    attachments: list[OperationsCommunicationAttachmentRead] = Field(
        default_factory=list,
    )


class OperationsCommunicationThreadRead(BaseModel):
    id: str
    customer_user_id: str | None
    customer_email: str | None
    assigned_user_id: str | None
    subject: str | None
    related_entity_type: str | None
    related_entity_id: str | None
    status: str
    last_message_at: str | None
    created_at: str
    message_count: int
    latest_direction: str | None
    latest_sender_address: str | None
    latest_subject: str | None
    failed_message_count: int
    mailbox_kind: str


class OperationsCommunicationThreadDetailRead(
    OperationsCommunicationThreadRead
):
    reply_target: str | None = None
    messages: list[OperationsCommunicationMessageRead] = Field(
        default_factory=list,
    )


class OperationsCommunicationThreadStatusUpdate(BaseModel):
    status: CommunicationThreadStatus


class OperationsCommunicationReplyCreate(BaseModel):
    body_text: str = Field(
        min_length=1,
        max_length=20000,
    )

    @field_validator("body_text")
    @classmethod
    def clean_body_text(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Reply message cannot be empty.")

        return cleaned


class OperationsCommunicationReplyRead(BaseModel):
    delivery_status: str
    recipient: str
    thread: OperationsCommunicationThreadDetailRead


class OperationsQuoteRead(BaseModel):
    id: str
    product_id: str | None
    product_name: str | None
    name: str
    email: str
    phone: str | None
    message: str | None
    recommendation_context: dict[str, object] | None
    recommendation_decision: dict[str, object] | None
    recommendation_policy_version: str | None
    internal_notes: str | None
    status: str
    created_at: str


class OperationsCustomerEquipmentRead(BaseModel):
    id: str
    product_id: str | None
    variant_id: str | None
    sku: str
    product_name: str
    variant_name: str | None
    serial_number: str | None
    location_label: str | None
    installed_on: str | None
    last_service_on: str | None
    next_service_due_on: str | None
    active: bool


class CustomerEquipmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    serial_number: str | None = Field(default=None, max_length=160)
    location_label: str | None = Field(default=None, max_length=160)
    installed_on: date | None = None
    last_service_on: date | None = None
    next_service_due_on: date | None = None

    @field_validator("serial_number", "location_label")
    @classmethod
    def clean_equipment_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CustomerEquipmentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    serial_number: str | None = Field(default=None, max_length=160)
    location_label: str | None = Field(default=None, max_length=160)
    installed_on: date | None = None
    last_service_on: date | None = None
    next_service_due_on: date | None = None
    active: bool = True

    @field_validator("serial_number", "location_label")
    @classmethod
    def clean_equipment_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


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
    equipment: list[OperationsCustomerEquipmentRead] = Field(default_factory=list)
    created_at: str


class OperationsOrderCustomerRead(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None


class OperationsOrderItemRead(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_amount_minor: int
    line_total_minor: int
    currency: str


class OperationsOrderRead(BaseModel):
    id: str
    status: str
    total_amount_minor: int
    currency: str
    created_at: str
    customer: OperationsOrderCustomerRead
    items: list[OperationsOrderItemRead] = Field(
        default_factory=list,
    )


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
    estimated_lead_time: str | None = None


class OperationsProductVariantRead(BaseModel):
    id: str
    sku: str
    display_name: str
    option_values: dict[str, str] = Field(default_factory=dict)


class OperationsProductRelationshipRead(BaseModel):
    id: str
    related_product_id: str
    related_sku: str
    related_name: str
    relationship_type: ProductRelationshipType
    public: bool
    active: bool
    sort_order: int


class OperationsProductRead(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    manufacturer: str
    product_family: str | None
    system_type: str | None
    active_variant_count: int
    variants: list[OperationsProductVariantRead] = Field(default_factory=list)
    public_option_count: int
    relationships: list[OperationsProductRelationshipRead] = Field(
        default_factory=list,
    )
    active: bool
    online_sale_approved: bool
    pricing: OperationsPricingRead
    inventory: OperationsInventoryRead


class ProductRelationshipCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    related_product_id: str
    relationship_type: ProductRelationshipType
    public: bool = False
    active: bool = True
    sort_order: int = Field(default=0, ge=0, le=10_000)


class ProductRelationshipUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type: ProductRelationshipType
    public: bool
    active: bool
    sort_order: int = Field(ge=0, le=10_000)


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
    model_config = ConfigDict(
        extra="forbid",
    )

    status: InventoryStatus
    quantity_on_hand: int = Field(
        ge=0,
        le=1_000_000,
    )
    estimated_lead_time: str | None = Field(
        default=None,
        max_length=120,
    )

    @field_validator("estimated_lead_time")
    @classmethod
    def normalize_estimated_lead_time(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

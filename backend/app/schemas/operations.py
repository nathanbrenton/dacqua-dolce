import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.core.email import normalize_email_address
from app.models.catalog import (
    InventorySourceKind,
    InventoryStatus,
    PricingPolicyMode,
    ProductRelationshipType,
    ReminderPreferenceKind,
)
from app.models.commerce import FulfillmentStatus
from app.models.communications import (
    CommunicationThreadStatus,
)
from app.models.quote import (
    QuoteRequestStatus,
)
from app.schemas.commercial import (
    CommercialAddressSnapshot,
    CommercialChargeInput,
    CommercialChargeRead,
    CommercialCostBreakdownRead,
)
from app.schemas.policies import FormalQuotePolicySnapshotRead


class OperationsSummaryRead(BaseModel):
    new_quotes: int
    open_quotes: int
    recommendation_human_review: int
    recommendation_lab_testing: int
    active_products: int
    failed_email_deliveries: int


class OperationsLaunchReadinessCheckRead(BaseModel):
    key: str
    label: str
    status: Literal["ready", "action_required", "deferred"]
    detail: str
    evidence: list[str] = Field(default_factory=list)


class OperationsLaunchReadinessRead(BaseModel):
    status: Literal["ready", "action_required", "deferred"]
    ready_count: int
    action_required_count: int
    deferred_count: int
    evaluated_at: str
    checks: list[OperationsLaunchReadinessCheckRead] = Field(default_factory=list)


class OperationsAuditEventRead(BaseModel):
    id: str
    actor_user_id: str | None
    actor_email: str | None
    action: str
    entity_type: str
    entity_id: str | None
    environment: str
    outcome: str
    request_id: str | None
    error_category: str | None
    endpoint: str | None
    error_code: str | None
    created_at: str


class OperationsAuditEventPageRead(BaseModel):
    items: list[OperationsAuditEventRead]
    page: int
    page_size: int
    has_more: bool


class OperationsCommunicationRead(BaseModel):
    id: str
    category: str
    related_entity_type: str | None
    related_entity_id: str | None
    sender: str
    recipient: str
    subject: str
    status: str
    requires_review: bool
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


class OperationsCommunicationOriginatingRequestRead(BaseModel):
    request_type: str
    name: str
    email: str
    phone: str | None
    product_name: str | None
    message: str | None
    created_at: str


class OperationsCommunicationThreadDetailRead(
    OperationsCommunicationThreadRead
):
    reply_target: str | None = None
    reply_target_source: str | None = None
    reply_sender_addresses: list[str] = Field(default_factory=list)
    reply_sender_default: str | None = None
    originating_request: OperationsCommunicationOriginatingRequestRead | None = None
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
    recipient: str | None = Field(
        default=None,
        max_length=320,
    )
    sender: str | None = Field(
        default=None,
        max_length=320,
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

    @field_validator("recipient")
    @classmethod
    def clean_recipient(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        parts = [
            item.strip()
            for item in value.replace(";", ",").split(",")
            if item.strip()
        ]

        if not parts:
            return None

        if len(parts) > 10:
            raise ValueError("Enter no more than 10 recipient email addresses.")

        recipients: list[str] = []
        seen: set[str] = set()

        try:
            for part in parts:
                address = normalize_email_address(part)

                if address in seen:
                    continue

                seen.add(address)
                recipients.append(address)
        except ValueError as exc:
            raise ValueError(
                "Enter valid recipient email addresses separated by commas or semicolons."
            ) from exc

        combined = ", ".join(recipients)

        if len(combined) > 320:
            raise ValueError(
                "The combined recipient addresses are too long."
            )

        return combined

    @field_validator("sender")
    @classmethod
    def clean_sender(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        try:
            return normalize_email_address(value)
        except ValueError as exc:
            raise ValueError("Select a valid sender email address.") from exc


class OperationsCommunicationReplyRead(BaseModel):
    delivery_status: str
    recipient: str
    recipients: list[str] = Field(default_factory=list)
    sender: str
    thread: OperationsCommunicationThreadDetailRead


class FormalQuoteItemCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1, le=100)
    unit_amount_minor: int | None = Field(default=None, ge=0)


class FormalQuoteCreate(BaseModel):
    items: list[FormalQuoteItemCreate] = Field(min_length=1, max_length=50)
    charges: list[CommercialChargeInput] = Field(default_factory=list, max_length=20)
    delivery_address: CommercialAddressSnapshot
    billing_address: CommercialAddressSnapshot
    customer_note: str | None = Field(default=None, max_length=4000)

    @field_validator("customer_note")
    @classmethod
    def clean_customer_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class OperationsFormalQuoteItemRead(BaseModel):
    id: str
    product_id: str | None
    variant_id: str | None
    sku: str
    name: str
    quantity: int
    unit_amount_minor: int
    line_total_minor: int
    currency: str
    pricing_policy_mode: str
    estimated_lead_time: str | None


class OperationsWarrantySnapshotRead(BaseModel):
    id: str
    sku: str
    product_name: str
    manufacturer_name: str
    title: str
    version: str
    path: str
    content_type: str
    checksum_sha256: str
    source_reference: str | None = None
    verified_at: str


class OperationsFormalQuoteRead(BaseModel):
    id: str
    revision_number: int
    status: str
    customer_user_id: str | None
    authored_by_user_id: str | None
    currency: str
    subtotal_amount_minor: int
    charges_amount_minor: int
    total_amount_minor: int
    cost_breakdown: CommercialCostBreakdownRead
    delivery_address: CommercialAddressSnapshot | None
    billing_address: CommercialAddressSnapshot | None
    charges: list[CommercialChargeRead] = Field(default_factory=list)
    policy_snapshots: list[FormalQuotePolicySnapshotRead] = Field(default_factory=list)
    warranty_snapshots: list[OperationsWarrantySnapshotRead] = Field(default_factory=list)
    shipping_insurance_offered: bool
    shipping_insurance_decision: str | None
    shipping_insurance_decided_at: str | None
    shipping_insurance_decided_by_user_id: str | None
    customer_note: str | None
    presented_at: str | None
    expires_at: str | None
    approved_at: str | None
    created_at: str
    items: list[OperationsFormalQuoteItemRead] = Field(default_factory=list)


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
    formal_quotes: list[OperationsFormalQuoteRead] = Field(default_factory=list)


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
    estimated_lead_time: str | None = None


class OperationsOrderShipmentRead(BaseModel):
    carrier: str
    tracking_number: str
    tracking_url: str | None
    shipped_at: str | None
    delivered_at: str | None


class OperationsOrderCancellationRead(BaseModel):
    id: str
    eligibility_mode: Literal[
        "unrestricted",
        "manual_review",
    ]
    status: Literal[
        "requested",
        "approved",
        "declined",
        "completed",
    ]
    reason: str | None
    review_note: str | None
    requested_at: str
    reviewed_at: str | None
    completed_at: str | None


class OperationsReturnPolicyExceptionRead(BaseModel):
    id: str
    actor_user_id: str | None
    created_at: str
    policy_snapshot_id: str
    policy_version: str
    reason: str
    return_window_days_override: int | None
    restocking_fee_basis_points_override: int | None
    customer_pays_return_shipping_override: bool | None
    refund_outbound_shipping_override: bool | None


class OrderReturnPolicyExceptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=4000)
    return_window_days_override: int | None = Field(
        default=None,
        ge=1,
        le=3650,
    )
    restocking_fee_basis_points_override: int | None = Field(
        default=None,
        ge=0,
        le=10_000,
    )
    customer_pays_return_shipping_override: bool | None = None
    refund_outbound_shipping_override: bool | None = None

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A reason is required.")
        return cleaned

    @model_validator(mode="after")
    def require_override(self) -> "OrderReturnPolicyExceptionCreate":
        if all(
            value is None
            for value in (
                self.return_window_days_override,
                self.restocking_fee_basis_points_override,
                self.customer_pays_return_shipping_override,
                self.refund_outbound_shipping_override,
            )
        ):
            raise ValueError(
                "At least one return-policy term must be overridden."
            )
        return self


class OperationsOrderRead(BaseModel):
    id: str
    status: str
    fulfillment_status: str
    cancellation_mode: Literal[
        "unrestricted",
        "manual_review",
    ]
    cancellation: OperationsOrderCancellationRead | None = None
    refund_policy_snapshot: FormalQuotePolicySnapshotRead | None = None
    return_policy_exceptions: list[
        OperationsReturnPolicyExceptionRead
    ] = Field(default_factory=list)
    supplier_order_reference: str | None
    supplier_ordered_at: str | None
    received_ready_at: str | None
    shipped_at: str | None
    delivered_at: str | None
    subtotal_amount_minor: int
    charges_amount_minor: int
    total_amount_minor: int
    currency: str
    delivery_address: CommercialAddressSnapshot | None
    billing_address: CommercialAddressSnapshot | None
    charges: list[CommercialChargeRead] = Field(default_factory=list)
    created_at: str
    customer: OperationsOrderCustomerRead
    items: list[OperationsOrderItemRead] = Field(
        default_factory=list,
    )
    shipment: OperationsOrderShipmentRead | None = None


class OrderCancellationReviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "approve",
        "decline",
        "complete",
    ]
    note: str | None = Field(
        default=None,
        max_length=4000,
    )

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class OrderFulfillmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: FulfillmentStatus
    supplier_order_reference: str | None = Field(
        default=None,
        max_length=160,
    )
    carrier: str | None = Field(
        default=None,
        max_length=100,
    )
    tracking_number: str | None = Field(
        default=None,
        max_length=200,
    )
    tracking_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    @field_validator(
        "supplier_order_reference",
        "carrier",
        "tracking_number",
        "tracking_url",
    )
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


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
    effective_until: str | None = None


class OperationsPromotionRead(BaseModel):
    id: str
    mode: str
    amount_minor: int
    currency: str
    effective_from: str
    effective_until: str
    state: Literal["scheduled", "active"]


class OperationsInventoryRead(BaseModel):
    status: str
    quantity_on_hand: int
    quantity_reserved: int
    estimated_lead_time: str | None = None
    source_kind: InventorySourceKind = InventorySourceKind.unspecified
    source_reference: str | None = None
    source_observed_at: str | None = None


class OperationsStockNotificationRead(BaseModel):
    id: str
    product_id: str
    product_sku: str
    product_name: str
    email: str
    active: bool
    notified_at: str | None
    created_at: str
    updated_at: str


class OperationsInsightBucketRead(BaseModel):
    value: str
    count: int


class OperationsSalesInsightsRead(BaseModel):
    total_requests: int
    structured_requests: int
    source_water: list[OperationsInsightBucketRead] = Field(default_factory=list)
    treatment_preference: list[OperationsInsightBucketRead] = Field(default_factory=list)
    service_postal_codes: list[OperationsInsightBucketRead] = Field(default_factory=list)
    limited_utility_requests: int
    lab_required_requests: int
    known_hardness_requests: int
    research_network_yes: int


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
    is_consumable: bool = False
    replacement_interval_days: int | None = None
    reminder_preference: ReminderPreferenceKind | None = None
    sort_order: int


class OperationsWarrantyDocumentRead(BaseModel):
    id: str
    title: str
    version: str
    path: str
    content_type: str
    checksum_sha256: str | None
    source_reference: str | None
    public: bool
    active: bool
    verified_at: str | None


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
    assisted_sale_required: bool
    online_sale_approved: bool
    warranty_documents: list[OperationsWarrantyDocumentRead] = Field(default_factory=list)
    pricing: OperationsPricingRead
    standard_pricing: OperationsPricingRead
    promotions: list[OperationsPromotionRead] = Field(default_factory=list)
    inventory: OperationsInventoryRead


class ProductRelationshipCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    related_product_id: str
    relationship_type: ProductRelationshipType
    public: bool = False
    active: bool = True
    is_consumable: bool = False
    replacement_interval_days: int | None = Field(default=None, ge=1, le=3650)
    reminder_preference: ReminderPreferenceKind | None = None
    sort_order: int = Field(default=0, ge=0, le=10_000)

    @model_validator(mode="after")
    def validate_consumable_interval(
        self,
    ) -> "ProductRelationshipCreateRequest":
        if self.replacement_interval_days is not None and not self.is_consumable:
            raise ValueError(
                "Replacement interval requires a consumable relationship."
            )
        if self.reminder_preference is not None and (
            not self.is_consumable
            or self.replacement_interval_days is None
        ):
            raise ValueError(
                "Reminder preference requires a consumable relationship "
                "with a supported replacement interval."
            )
        return self


class ProductRelationshipUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type: ProductRelationshipType
    public: bool
    active: bool
    is_consumable: bool = False
    replacement_interval_days: int | None = Field(default=None, ge=1, le=3650)
    reminder_preference: ReminderPreferenceKind | None = None
    sort_order: int = Field(ge=0, le=10_000)

    @model_validator(mode="after")
    def validate_consumable_interval(
        self,
    ) -> "ProductRelationshipUpdateRequest":
        if self.replacement_interval_days is not None and not self.is_consumable:
            raise ValueError(
                "Replacement interval requires a consumable relationship."
            )
        if self.reminder_preference is not None and (
            not self.is_consumable
            or self.replacement_interval_days is None
        ):
            raise ValueError(
                "Reminder preference requires a consumable relationship "
                "with a supported replacement interval."
            )
        return self


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


class PromotionCreateRequest(BaseModel):
    amount_minor: int = Field(gt=0)
    effective_from: datetime
    effective_until: datetime

    @model_validator(mode="after")
    def validate_window(self) -> "PromotionCreateRequest":
        if self.effective_from.tzinfo is None or self.effective_until.tzinfo is None:
            raise ValueError("Promotion timestamps must include a timezone.")
        if self.effective_until <= self.effective_from:
            raise ValueError("Promotion end must be after its start.")
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
    source_kind: InventorySourceKind = InventorySourceKind.operator_entry
    source_reference: str | None = Field(
        default=None,
        max_length=240,
    )

    @field_validator("estimated_lead_time", "source_reference")
    @classmethod
    def normalize_optional_inventory_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

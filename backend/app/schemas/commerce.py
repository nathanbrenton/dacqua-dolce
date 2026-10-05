from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.commercial import (
    CommercialAddressSnapshot,
    CommercialChargeRead,
)


class CartItemCreate(BaseModel):
    product_id: str
    variant_id: str | None = None
    quantity: int = Field(
        default=1,
        ge=1,
        le=99,
    )


class CartItemRead(BaseModel):
    id: str
    product_id: str
    variant_id: str | None
    sku: str
    name: str
    quantity: int
    unit_amount_minor: int
    line_total_minor: int
    currency: str


class CartRead(BaseModel):
    id: str
    status: str
    items: list[CartItemRead]
    total_amount_minor: int
    currency: str | None


class OrderItemRead(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_amount_minor: int
    line_total_minor: int
    currency: str
    estimated_lead_time: str | None = None


class OrderShipmentRead(BaseModel):
    carrier: str
    tracking_number: str
    tracking_url: str | None
    shipped_at: str | None
    delivered_at: str | None


class OrderCancellationRequestCreate(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator("reason")
    @classmethod
    def clean_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class OrderCancellationRead(BaseModel):
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
    requested_at: str
    reviewed_at: str | None
    completed_at: str | None


class OrderRead(BaseModel):
    id: str
    formal_quote_id: str | None
    status: str
    fulfillment_status: str
    customer_status: Literal[
        "received",
        "processing",
        "supplier_confirmed",
        "awaiting_shipment",
        "shipped",
        "completed",
        "cancelled",
        "refunded",
    ]
    cancellation_mode: Literal[
        "unrestricted",
        "closed_after_supplier_confirmation",
    ]
    cancellation: OrderCancellationRead | None = None
    subtotal_amount_minor: int
    charges_amount_minor: int
    total_amount_minor: int
    currency: str
    delivery_address: CommercialAddressSnapshot | None
    billing_address: CommercialAddressSnapshot | None
    charges: list[CommercialChargeRead] = Field(default_factory=list)
    created_at: str
    items: list[OrderItemRead]
    shipment: OrderShipmentRead | None = None

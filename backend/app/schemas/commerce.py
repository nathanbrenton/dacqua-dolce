from pydantic import BaseModel, Field


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


class OrderRead(BaseModel):
    id: str
    status: str
    total_amount_minor: int
    currency: str
    created_at: str
    items: list[OrderItemRead]

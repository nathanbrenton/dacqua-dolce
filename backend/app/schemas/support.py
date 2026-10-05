from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.email import normalize_email_address
from app.core.phone import normalize_us_phone

SupportRequestKind = Literal[
    "warranty",
    "product_support",
    "general_support",
]


class SupportRequestCreate(BaseModel):
    kind: SupportRequestKind
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    product_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("name", "message")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank.")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return normalize_email_address(value)

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Phone number must be text.")
        return normalize_us_phone(value)


class SupportRequestRead(BaseModel):
    id: str
    status: Literal["received"] = "received"
    message: str

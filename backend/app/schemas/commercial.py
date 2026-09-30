from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.quote import CommercialChargeKind


class CommercialAddressSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_name: str = Field(min_length=1, max_length=200)
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=120)
    region_code: str = Field(min_length=1, max_length=32)
    postal_code: str = Field(min_length=1, max_length=32)
    country_code: str = Field(default="US", min_length=2, max_length=2)
    phone: str | None = Field(default=None, max_length=50)

    @field_validator(
        "recipient_name",
        "line1",
        "city",
        "region_code",
        "postal_code",
        "country_code",
    )
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Address fields cannot be blank.")
        return cleaned

    @field_validator("line2", "phone")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized.isalpha():
            raise ValueError("country_code must contain two letters.")
        return normalized


class CommercialChargeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: CommercialChargeKind
    label: str = Field(min_length=1, max_length=160)
    amount_minor: int

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Commercial charge labels cannot be blank.")
        return cleaned

    @model_validator(mode="after")
    def validate_sign(self) -> "CommercialChargeInput":
        positive_kinds = {
            CommercialChargeKind.shipping,
            CommercialChargeKind.tax,
            CommercialChargeKind.installation,
            CommercialChargeKind.other_charge,
        }
        credit_kinds = {
            CommercialChargeKind.discount,
            CommercialChargeKind.other_credit,
        }
        if self.kind in positive_kinds and self.amount_minor <= 0:
            raise ValueError("Charge amounts must be greater than zero.")
        if self.kind in credit_kinds and self.amount_minor >= 0:
            raise ValueError("Discount and credit amounts must be negative.")
        return self


class CommercialChargeRead(BaseModel):
    kind: CommercialChargeKind
    label: str
    amount_minor: int

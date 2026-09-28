from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from app.core.email import (
    normalize_email_address,
)
from app.core.phone import (
    normalize_us_phone,
)


TriState = Literal["yes", "no", "unsure"]


class RecommendationContext(BaseModel):
    source_water: Literal["municipal", "well", "unsure"]
    hard_water_signs: TriState
    bathrooms: Literal["1", "2", "3", "4", "5+", "unsure"]
    water_quality_report_read: TriState
    chlorine_chloramine_signs: TriState
    iron_manganese_concerns: TriState
    existing_equipment: str | None = Field(
        default=None,
        max_length=1000,
    )
    drain_available: TriState
    electrical_available: TriState
    irrigation_hose_bib: TriState
    pool_autofill: TriState
    drinking_water_ro: TriState
    water_test_results: TriState
    water_filtration_network: TriState
    treatment_preference: Literal[
        "salt_free",
        "softened",
        "unsure",
    ]

    @field_validator("existing_equipment")
    @classmethod
    def clean_existing_equipment(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class QuoteRequestCreate(BaseModel):
    product_id: str | None = None

    name: str = Field(
        min_length=1,
        max_length=160,
    )

    email: str = Field(
        min_length=3,
        max_length=320,
    )

    phone: str | None = Field(
        default=None,
        max_length=50,
    )

    message: str | None = Field(
        default=None,
        max_length=4000,
    )

    recommendation_context: RecommendationContext | None = None

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: str,
    ) -> str:
        return normalize_email_address(value)

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

    @field_validator("message")
    @classmethod
    def clean_optional_message(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


class QuoteRequestRead(BaseModel):
    id: str
    status: str

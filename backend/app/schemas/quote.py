from pydantic import BaseModel, Field, field_validator


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

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()

        if "@" not in normalized:
            raise ValueError("A valid email address is required.")

        return normalized

    @field_validator("phone", "message")
    @classmethod
    def clean_optional_text(
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

from pydantic import BaseModel, Field, field_validator


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
        "phone",
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


class CustomerProfileRead(BaseModel):
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    addresses: list[AddressRead] = Field(default_factory=list)

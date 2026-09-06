from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class PasswordResetRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        if "@" not in normalized:
            raise ValueError("A valid email address is required.")

        return normalized


class PasswordResetCompleteRequest(BaseModel):
    token: str = Field(
        min_length=20,
        max_length=512,
    )

    password: str = Field(
        min_length=12,
        max_length=256,
    )


class PasswordResetResponse(BaseModel):
    message: str

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        min_length=1,
        max_length=256,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AccountRegistrationRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        min_length=12,
        max_length=256,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()

        if "@" not in normalized:
            raise ValueError("A valid email address is required.")

        return normalized


class AuthenticationStatus(BaseModel):
    authenticated: bool
    email: str | None = None
    roles: list[str] = Field(default_factory=list)


class UserSessionRead(BaseModel):
    id: str
    created_at: str
    last_seen_at: str | None
    expires_at: str
    ip_address: str | None
    user_agent: str | None
    current: bool


class SessionListResponse(BaseModel):
    sessions: list[UserSessionRead]

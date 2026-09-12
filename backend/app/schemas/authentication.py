from pydantic import BaseModel, Field, field_validator

from app.core.email import normalize_email_address


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
        return normalize_email_address(value)


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
        return normalize_email_address(value)


class AuthenticationStatus(BaseModel):
    authenticated: bool
    email: str | None = None
    roles: list[str] = Field(default_factory=list)
    mfa_required: bool = False
    mfa_enrollment_required: bool = False


class MfaEnrollmentResponse(BaseModel):
    secret: str
    provisioning_uri: str
    recovery_codes: list[str]


class MfaVerificationRequest(BaseModel):
    code: str = Field(
        min_length=6,
        max_length=64,
    )


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

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import (
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class EmailRuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DACQUA_",
        extra="ignore",
    )

    public_origin: str = "http://127.0.0.1:5173"

    email_provider: Literal[
        "disabled",
        "postmark",
    ] = "disabled"

    postmark_server_token: SecretStr | None = None

    email_from: str = "no-reply@localhost.invalid"

    email_operator_to: str | None = None

    password_reset_ttl_minutes: int = Field(
        default=30,
        ge=5,
        le=120,
    )

    @field_validator("public_origin")
    @classmethod
    def validate_public_origin(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().rstrip("/")

        parsed = urlsplit(normalized)

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("public_origin must be an absolute HTTP(S) origin.")

        local_hosts = {
            "localhost",
            "127.0.0.1",
            "::1",
        }

        if parsed.hostname not in local_hosts and parsed.scheme != "https":
            raise ValueError("Non-local public origins must use HTTPS.")

        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("public_origin must contain only scheme and authority.")

        return normalized

    def public_url(
        self,
        path: str,
    ) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"

        return f"{self.public_origin}{normalized_path}"

    @property
    def postmark_token_value(
        self,
    ) -> str | None:
        if self.postmark_server_token is None:
            return None

        value = self.postmark_server_token.get_secret_value().strip()

        return value or None


@lru_cache
def get_email_runtime_settings() -> EmailRuntimeSettings:
    return EmailRuntimeSettings()

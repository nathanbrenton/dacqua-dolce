import uuid
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

from app.core.email import normalize_email_address


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

    postmark_inbound_webhook_username: SecretStr | None = None
    postmark_inbound_webhook_password: SecretStr | None = None
    postmark_inbound_address: str | None = None

    email_from: str = "no-reply@localhost.invalid"
    email_support_from: str | None = None

    email_operator_to: str | None = None

    password_reset_ttl_minutes: int = Field(
        default=30,
        ge=5,
        le=120,
    )

    email_verification_ttl_minutes: int = Field(
        default=24 * 60,
        ge=15,
        le=7 * 24 * 60,
    )

    @field_validator("postmark_inbound_address")
    @classmethod
    def validate_postmark_inbound_address(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        if not stripped:
            return None

        normalized = normalize_email_address(stripped)
        local_part, _ = normalized.rsplit("@", 1)

        if "+" in local_part:
            raise ValueError(
                "postmark_inbound_address must be the base inbound mailbox."
            )

        return normalized

    @field_validator("email_support_from")
    @classmethod
    def validate_email_support_from(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        if not stripped:
            return None

        return normalize_email_address(stripped)

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

    def postmark_thread_reply_to(
        self,
        thread_id: uuid.UUID,
    ) -> str | None:
        if self.postmark_inbound_address is None:
            return None

        local_part, domain = self.postmark_inbound_address.rsplit("@", 1)
        return f"{local_part}+{thread_id}@{domain}"

    @staticmethod
    def _secret_value(
        value: SecretStr | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.get_secret_value().strip()
        return normalized or None

    @property
    def postmark_token_value(
        self,
    ) -> str | None:
        return self._secret_value(self.postmark_server_token)

    @property
    def postmark_inbound_webhook_username_value(
        self,
    ) -> str | None:
        return self._secret_value(
            self.postmark_inbound_webhook_username
        )

    @property
    def postmark_inbound_webhook_password_value(
        self,
    ) -> str | None:
        return self._secret_value(
            self.postmark_inbound_webhook_password
        )


@lru_cache
def get_email_runtime_settings() -> EmailRuntimeSettings:
    return EmailRuntimeSettings()

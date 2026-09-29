import uuid
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import (
    Field,
    SecretStr,
    field_validator,
    model_validator,
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

    environment: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    public_origin: str = "http://127.0.0.1:15173"

    email_provider: Literal[
        "disabled",
        "postmark",
    ] = "disabled"

    postmark_server_token: SecretStr | None = None

    postmark_inbound_webhook_username: SecretStr | None = None
    postmark_inbound_webhook_password: SecretStr | None = None
    postmark_inbound_address: str | None = None

    email_from: str = "no-reply@dacquadolce.test"
    email_support_from: str | None = None
    email_reply_from_addresses: str | None = None

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

    @property
    def company_email_domain(self) -> str:
        if self.environment == "production":
            return "dacquadolce.com"

        return "dacquadolce.test"

    @property
    def default_company_reply_from_addresses(
        self,
    ) -> tuple[str, ...]:
        domain = self.company_email_domain

        return (
            f"sales@{domain}",
            f"contact@{domain}",
            f"info@{domain}",
            f"support@{domain}",
        )

    @model_validator(mode="after")
    def apply_environment_email_defaults(
        self,
    ) -> "EmailRuntimeSettings":
        default_sender_addresses = {
            "no-reply@localhost.invalid",
            "no-reply@dacquadolce.test",
        }

        if self.email_from in default_sender_addresses:
            self.email_from = (
                f"no-reply@{self.company_email_domain}"
            )

        return self

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

    @field_validator("email_reply_from_addresses")
    @classmethod
    def validate_email_reply_from_addresses(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        candidates = [
            item.strip()
            for item in value.replace(";", ",").split(",")
            if item.strip()
        ]

        if not candidates:
            return None

        if len(candidates) > 20:
            raise ValueError(
                "email_reply_from_addresses supports at most 20 addresses."
            )

        normalized: list[str] = []
        seen: set[str] = set()

        for candidate in candidates:
            address = normalize_email_address(candidate)

            if address in seen:
                continue

            seen.add(address)
            normalized.append(address)

        return ",".join(normalized)

    @property
    def communication_reply_from_addresses(
        self,
    ) -> tuple[str, ...]:
        configured = (
            self.email_reply_from_addresses.split(",")
            if self.email_reply_from_addresses
            else list(self.default_company_reply_from_addresses)
        )

        candidates = [
            *configured,
            self.email_support_from,
            self.email_from,
        ]

        addresses: list[str] = []
        seen: set[str] = set()

        for candidate in candidates:
            if candidate is None:
                continue

            address = normalize_email_address(candidate)

            if address in seen:
                continue

            seen.add(address)
            addresses.append(address)

        return tuple(addresses)

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

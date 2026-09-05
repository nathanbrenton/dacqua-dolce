import hashlib
import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
MAX_LOG_VALUE_LENGTH = 512

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "current_password",
    "new_password",
    "token",
    "access_token",
    "refresh_token",
    "session_token",
    "csrf_token",
    "reset_token",
    "webhook_secret",
    "signature",
    "api_key",
    "secret",
    "client_secret",
    "pan",
    "primary_account_number",
    "card_number",
    "cvv",
    "cvc",
    "security_code",
    "expiration",
    "expiration_date",
    "track_data",
    "track1",
    "track2",
    "pin",
    "pin_block",
}

TOKEN_QUERY_PATTERN = re.compile(r"(?i)(token|signature|key|secret|password)=([^&\s]+)")
PAN_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,19}(?!\d)")


def normalized_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_")


def is_sensitive_key(value: object) -> bool:
    key = normalized_key(value)

    return key in {item.replace("-", "_") for item in SENSITIVE_KEYS} or any(
        marker in key
        for marker in (
            "password",
            "secret",
            "authorization",
            "cookie",
            "csrf",
            "reset_token",
            "webhook_signature",
            "card_number",
        )
    )


def sanitize_text(
    value: str,
    *,
    max_length: int = MAX_LOG_VALUE_LENGTH,
) -> str:
    sanitized = value.replace("\r", " ").replace("\n", " ")
    sanitized = TOKEN_QUERY_PATTERN.sub(
        rf"\1={REDACTED}",
        sanitized,
    )
    sanitized = PAN_PATTERN.sub(REDACTED, sanitized)

    if len(sanitized) > max_length:
        return sanitized[: max_length - 3] + "..."

    return sanitized


def sanitize_value(value: Any, *, depth: int = 0) -> Any:
    if depth > 6:
        return "[MAX_DEPTH]"

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}

        for key, item in value.items():
            key_text = sanitize_text(str(key), max_length=120)

            result[key_text] = (
                REDACTED if is_sensitive_key(key) else sanitize_value(item, depth=depth + 1)
            )

        return result

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [sanitize_value(item, depth=depth + 1) for item in list(value)[:100]]

    if isinstance(value, bytes):
        return f"[BYTES:{len(value)}]"

    if isinstance(value, str):
        return sanitize_text(value)

    if value is None or isinstance(value, (bool, int, float)):
        return value

    return sanitize_text(str(value))


def privacy_safe_identifier(value: str | None) -> str | None:
    if value is None:
        return None

    return hashlib.sha256(value.strip().lower().encode()).hexdigest()[:16]

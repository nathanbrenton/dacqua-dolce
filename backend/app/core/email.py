import re

EMAIL_PATTERN = re.compile(
    r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
)


def normalize_email_address(
    value: str,
) -> str:
    """Normalize and validate a basic Internet email address."""

    normalized = value.strip().lower()

    if EMAIL_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            "A valid email address is required."
        )

    return normalized

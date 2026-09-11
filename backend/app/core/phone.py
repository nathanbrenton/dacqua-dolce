import re

_ALLOWED_PHONE_CHARACTERS = re.compile(r"^[0-9+().\-\s]+$")


def normalize_us_phone(
    value: str | None,
) -> str | None:
    """Normalize a US/NANP phone number to E.164."""

    if value is None:
        return None

    cleaned = value.strip()

    if not cleaned:
        return None

    if not _ALLOWED_PHONE_CHARACTERS.fullmatch(cleaned):
        raise ValueError("Phone numbers may contain only digits and common phone punctuation.")

    digits = "".join(character for character in cleaned if "0" <= character <= "9")

    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    if len(digits) != 10:
        raise ValueError("Enter a 10-digit US phone number.")

    if digits[0] in {"0", "1"}:
        raise ValueError("The area code must begin with 2 through 9.")

    if digits[3] in {"0", "1"}:
        raise ValueError("The exchange must begin with 2 through 9.")

    return f"+1{digits}"

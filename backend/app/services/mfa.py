import base64
import hashlib
import hmac
import secrets
import struct
from datetime import UTC, datetime
from urllib.parse import quote, urlencode

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)

from app.core.config import Settings
from app.models.identity import (
    RoleName,
    User,
)

PRIVILEGED_MFA_ROLES = frozenset(
    {
        RoleName.manager,
        RoleName.administrator,
        RoleName.developer,
    }
)


class MfaConfigurationError(
    RuntimeError,
):
    pass


def user_requires_mfa(
    user: User,
) -> bool:
    roles = {
        assignment.role
        for assignment in user.roles
    }

    return bool(
        roles.intersection(
            PRIVILEGED_MFA_ROLES
        )
    )


def _fernet(
    settings: Settings,
) -> Fernet:
    key = settings.mfa_encryption_key

    if key is None or not key.strip():
        raise MfaConfigurationError(
            "MFA encryption key is not configured."
        )

    try:
        return Fernet(
            key.encode("ascii")
        )
    except (
        ValueError,
        TypeError,
    ) as exc:
        raise MfaConfigurationError(
            "MFA encryption key is invalid."
        ) from exc


def encrypt_totp_secret(
    secret: str,
    settings: Settings,
) -> str:
    return (
        _fernet(settings)
        .encrypt(
            secret.encode("ascii")
        )
        .decode("ascii")
    )


def decrypt_totp_secret(
    ciphertext: str,
    settings: Settings,
) -> str:
    try:
        return (
            _fernet(settings)
            .decrypt(
                ciphertext.encode("ascii")
            )
            .decode("ascii")
        )
    except InvalidToken as exc:
        raise MfaConfigurationError(
            "Unable to decrypt MFA secret."
        ) from exc


def generate_totp_secret() -> str:
    return (
        base64.b32encode(
            secrets.token_bytes(20)
        )
        .decode("ascii")
        .rstrip("=")
    )


def _decode_base32(
    secret: str,
) -> bytes:
    normalized = (
        secret.strip()
        .replace(" ", "")
        .upper()
    )

    padding = (
        "="
        * (
            (
                8
                - len(normalized) % 8
            )
            % 8
        )
    )

    return base64.b32decode(
        normalized + padding,
        casefold=True,
    )


def totp_code(
    secret: str,
    *,
    at_time: datetime | None = None,
    period_seconds: int = 30,
    digits: int = 6,
) -> str:
    effective_time = (
        at_time
        if at_time is not None
        else datetime.now(UTC)
    )

    counter = (
        int(
            effective_time.timestamp()
        )
        // period_seconds
    )

    digest = hmac.new(
        _decode_base32(secret),
        struct.pack(
            ">Q",
            counter,
        ),
        hashlib.sha1,
    ).digest()

    offset = (
        digest[-1]
        & 0x0F
    )

    value = (
        int.from_bytes(
            digest[
                offset:
                offset + 4
            ],
            "big",
        )
        & 0x7FFFFFFF
    )

    return str(
        value
        % (10**digits)
    ).zfill(digits)


def verify_totp(
    secret: str,
    code: str,
    *,
    settings: Settings,
    at_time: datetime | None = None,
) -> bool:
    normalized = code.strip()

    if (
        len(normalized)
        != settings.mfa_totp_digits
        or not normalized.isdigit()
    ):
        return False

    effective_time = (
        at_time
        if at_time is not None
        else datetime.now(UTC)
    )

    for offset in range(
        -settings.mfa_totp_valid_window,
        settings.mfa_totp_valid_window
        + 1,
    ):
        candidate_time = (
            effective_time.timestamp()
            + (
                offset
                * settings.mfa_totp_period_seconds
            )
        )

        candidate = totp_code(
            secret,
            at_time=datetime.fromtimestamp(
                candidate_time,
                tz=UTC,
            ),
            period_seconds=(
                settings.mfa_totp_period_seconds
            ),
            digits=settings.mfa_totp_digits,
        )

        if secrets.compare_digest(
            candidate,
            normalized,
        ):
            return True

    return False


def generate_recovery_code() -> str:
    raw = secrets.token_hex(
        12,
    ).upper()

    return "-".join(
        raw[index:index + 4]
        for index in range(
            0,
            len(raw),
            4,
        )
    )


def generate_recovery_codes(
    count: int,
) -> list[str]:
    return [
        generate_recovery_code()
        for _ in range(count)
    ]


def normalize_recovery_code(
    code: str,
) -> str:
    return (
        code.strip()
        .replace("-", "")
        .replace(" ", "")
        .upper()
    )


def hash_recovery_code(
    code: str,
) -> str:
    return hashlib.sha256(
        normalize_recovery_code(
            code
        ).encode("ascii")
    ).hexdigest()


def build_provisioning_uri(
    *,
    issuer: str,
    email: str,
    secret: str,
    period_seconds: int,
    digits: int,
) -> str:
    label = (
        f"{issuer}:{email}"
    )

    query = urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": str(digits),
            "period": str(
                period_seconds
            ),
        }
    )

    return (
        "otpauth://totp/"
        + quote(
            label,
            safe="",
        )
        + "?"
        + query
    )

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from app.models.identity import UserSession

SESSION_TOKEN_BYTES = 32
SESSION_DURATION = timedelta(hours=12)


def generate_session_token() -> str:
    """Generate a cryptographically random opaque session token."""

    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """Generate the one-way token digest stored in PostgreSQL."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_session(
    *,
    user_id: uuid.UUID,
    token: str,
    ip_address: str | None,
    user_agent: str | None,
) -> UserSession:
    """Build a persistent session without storing its raw token."""

    now = datetime.now(UTC)

    return UserSession(
        user_id=user_id,
        token_hash=hash_session_token(token),
        expires_at=now + SESSION_DURATION,
        last_seen_at=now,
        ip_address=ip_address,
        user_agent=user_agent,
    )

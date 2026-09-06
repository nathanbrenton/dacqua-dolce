import hashlib
import secrets
from datetime import (
    UTC,
    datetime,
    timedelta,
)

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.email_config import (
    EmailRuntimeSettings,
)
from app.integrations.email import (
    EmailMessage,
)
from app.models.identity import (
    User,
    UserCredential,
    UserSession,
    UserStatus,
)
from app.models.recovery import (
    PasswordResetToken,
)
from app.services.audit import (
    record_audit_event,
)
from app.services.email_delivery import (
    deliver_email,
)

password_hasher = PasswordHash.recommended()

GENERIC_RESET_MESSAGE = (
    "If an account exists for that email address, a password reset link will be sent."
)


def generate_reset_token() -> str:
    return secrets.token_urlsafe(48)


def hash_reset_token(
    token: str,
) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_password_reset(
    db: Session,
    *,
    user: User,
    settings: EmailRuntimeSettings,
    requested_ip_address: (str | None),
    requested_user_agent: (str | None),
) -> None:
    now = datetime.now(UTC)

    existing_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.superseded_at.is_(None),
        )
    ).all()

    for existing in existing_tokens:
        existing.superseded_at = now

    raw_token = generate_reset_token()

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=(now + timedelta(minutes=(settings.password_reset_ttl_minutes))),
        requested_ip_address=(requested_ip_address),
        requested_user_agent=(requested_user_agent),
    )

    db.add(reset_record)
    db.flush()

    reset_url = settings.public_url(f"/reset-password/{raw_token}")

    subject = "Reset your D'Acqua Dolce password"

    body_text = (
        "A password reset was "
        "requested for your "
        "D'Acqua Dolce account.\n\n"
        "Use this single-use link "
        f"within "
        f"{settings.password_reset_ttl_minutes} "
        f"minutes:\n{reset_url}\n\n"
        "If you did not request this, "
        "you can ignore this email."
    )

    body_html = (
        "<p>A password reset was "
        "requested for your "
        "D&apos;Acqua Dolce account."
        "</p>"
        "<p>"
        f'<a href="{reset_url}">'
        "Reset your password"
        "</a>"
        "</p>"
        "<p>This single-use link "
        f"expires in "
        f"{settings.password_reset_ttl_minutes} "
        "minutes.</p>"
        "<p>If you did not request "
        "this, you can ignore this "
        "email.</p>"
    )

    deliver_email(
        db,
        settings=settings,
        message=EmailMessage(
            sender=settings.email_from,
            recipient=user.email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        ),
        category="password_reset",
        related_entity_type="user",
        related_entity_id=str(user.id),
    )

    record_audit_event(
        db,
        action=("authentication.password_reset_issued"),
        entity_type="user",
        entity_id=str(user.id),
        metadata={"expires_at": (reset_record.expires_at.isoformat())},
        ip_address=(requested_ip_address),
        user_agent=(requested_user_agent),
    )


def complete_password_reset(
    db: Session,
    *,
    raw_token: str,
    new_password: str,
    request_ip_address: str | None,
    request_user_agent: str | None,
) -> bool:
    now = datetime.now(UTC)

    token_record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_reset_token(raw_token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.superseded_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )

    if token_record is None:
        return False

    user = db.get(
        User,
        token_record.user_id,
    )

    credential = db.get(
        UserCredential,
        token_record.user_id,
    )

    if user is None or credential is None or user.status != UserStatus.active:
        token_record.superseded_at = now
        db.flush()

        return False

    if (
        credential.password_changed_at is not None
        and credential.password_changed_at > token_record.created_at
    ):
        token_record.superseded_at = now
        db.flush()

        return False

    credential.password_hash = password_hasher.hash(new_password)
    credential.password_changed_at = now

    user.failed_login_count = 0
    user.locked_until = None

    token_record.used_at = now

    other_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != token_record.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.superseded_at.is_(None),
        )
    ).all()

    for other in other_tokens:
        other.superseded_at = now

    sessions = db.scalars(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
    ).all()

    for session in sessions:
        session.revoked_at = now

    record_audit_event(
        db,
        action=("authentication.password_reset_completed"),
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
        ip_address=(request_ip_address),
        user_agent=(request_user_agent),
    )

    db.flush()

    return True

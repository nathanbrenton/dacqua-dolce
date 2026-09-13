import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.email_config import EmailRuntimeSettings
from app.integrations.email import EmailMessage
from app.models.email_verification import (
    EmailVerificationToken,
)
from app.models.identity import User, UserStatus
from app.services.audit import record_audit_event
from app.services.email_delivery import deliver_email

GENERIC_VERIFICATION_MESSAGE = (
    "If email verification is needed, "
    "a verification link will be sent."
)


def generate_verification_token() -> str:
    return secrets.token_urlsafe(48)


def hash_verification_token(
    token: str,
) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def issue_email_verification(
    db: Session,
    *,
    user: User,
    settings: EmailRuntimeSettings,
    requested_ip_address: str | None,
    requested_user_agent: str | None,
) -> str | None:
    if (
        user.status != UserStatus.active
        or user.email_verified_at is not None
    ):
        return None

    now = datetime.now(UTC)

    existing = db.scalars(
        select(
            EmailVerificationToken
        ).where(
            EmailVerificationToken.user_id
            == user.id,
            EmailVerificationToken.used_at.is_(
                None
            ),
            EmailVerificationToken
            .superseded_at.is_(None),
        )
    ).all()

    for token in existing:
        token.superseded_at = now

    raw_token = generate_verification_token()

    token_record = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_verification_token(
            raw_token
        ),
        expires_at=(
            now
            + timedelta(
                minutes=(
                    settings
                    .email_verification_ttl_minutes
                )
            )
        ),
        requested_ip_address=(
            requested_ip_address
        ),
        requested_user_agent=(
            requested_user_agent
        ),
    )

    db.add(token_record)
    db.flush()

    verification_url = settings.public_url(
        f"/verify-email/{raw_token}"
    )

    ttl_hours = (
        settings.email_verification_ttl_minutes
        / 60
    )

    subject = (
        "Verify your D'Acqua Dolce email"
    )

    body_text = (
        "Verify the email address for "
        "your D'Acqua Dolce account.\n\n"
        "Verification link:\n"
        f"{verification_url}\n\n"
        "This single-use link expires in "
        f"{ttl_hours:g} hours.\n\n"
        "If you did not create this "
        "account, you can ignore this email."
    )

    body_html = (
        "<p>Verify the email address for "
        "your D&apos;Acqua Dolce account."
        "</p>"
        "<p>"
        f'<a href="{verification_url}">'
        "Verify email address"
        "</a>"
        "</p>"
        "<p>This single-use link expires "
        f"in {ttl_hours:g} hours.</p>"
        "<p>If you did not create this "
        "account, you can ignore this "
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
        category="email_verification",
        related_entity_type="user",
        related_entity_id=str(user.id),
    )

    record_audit_event(
        db,
        action=(
            "authentication."
            "email_verification_issued"
        ),
        entity_type="user",
        entity_id=str(user.id),
        metadata={
            "expires_at": (
                token_record
                .expires_at
                .isoformat()
            ),
        },
        ip_address=requested_ip_address,
        user_agent=requested_user_agent,
    )

    return raw_token


def complete_email_verification(
    db: Session,
    *,
    raw_token: str,
    request_ip_address: str | None,
    request_user_agent: str | None,
) -> bool:
    now = datetime.now(UTC)

    token_record = db.scalar(
        select(
            EmailVerificationToken
        ).where(
            EmailVerificationToken.token_hash
            == hash_verification_token(
                raw_token
            ),
            EmailVerificationToken.used_at.is_(
                None
            ),
            EmailVerificationToken
            .superseded_at.is_(None),
            EmailVerificationToken.expires_at
            > now,
        )
    )

    if token_record is None:
        return False

    user = db.get(
        User,
        token_record.user_id,
    )

    if (
        user is None
        or user.status != UserStatus.active
    ):
        token_record.superseded_at = now
        db.flush()
        return False

    user.email_verified_at = now
    token_record.used_at = now

    other_tokens = db.scalars(
        select(
            EmailVerificationToken
        ).where(
            EmailVerificationToken.user_id
            == user.id,
            EmailVerificationToken.id
            != token_record.id,
            EmailVerificationToken.used_at.is_(
                None
            ),
            EmailVerificationToken
            .superseded_at.is_(None),
        )
    ).all()

    for other in other_tokens:
        other.superseded_at = now

    record_audit_event(
        db,
        action=(
            "authentication."
            "email_verification_completed"
        ),
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
        ip_address=request_ip_address,
        user_agent=request_user_agent,
    )

    db.flush()

    return True

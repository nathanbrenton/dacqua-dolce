from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import User, UserCredential, UserStatus
from app.services.passwords import verify_password

MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
) -> User | None:
    normalized_email = email.strip().lower()

    user = db.scalar(select(User).where(User.email == normalized_email))

    if user is None or user.credential is None:
        return None

    now = datetime.now(UTC)

    if user.status == UserStatus.disabled:
        return None

    if user.locked_until is not None and user.locked_until > now:
        return None

    if not verify_password(
        password,
        user.credential.password_hash,
    ):
        user.failed_login_count += 1

        if user.failed_login_count >= MAX_FAILED_LOGINS:
            user.status = UserStatus.locked
            user.locked_until = now + LOCKOUT_DURATION

        db.flush()
        return None

    user.failed_login_count = 0
    user.locked_until = None
    user.status = UserStatus.active
    user.last_login_at = now

    db.flush()

    return user


def attach_password(
    user: User,
    password_hash: str,
) -> None:
    user.credential = UserCredential(password_hash=password_hash)

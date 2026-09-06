from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select

from app.core.email_config import (
    get_email_runtime_settings,
)
from app.core.privacy import (
    privacy_safe_identifier,
)
from app.db.session import SessionLocal
from app.models.identity import (
    User,
    UserStatus,
)
from app.schemas.password_reset import (
    PasswordResetCompleteRequest,
    PasswordResetRequest,
    PasswordResetResponse,
)
from app.services.audit import (
    record_audit_event,
)
from app.services.auth_rate_limit import (
    AuthenticationRateLimiter,
)
from app.services.password_reset import (
    GENERIC_RESET_MESSAGE,
    complete_password_reset,
    issue_password_reset,
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

request_ip_limiter = AuthenticationRateLimiter(
    window_seconds=15 * 60,
    max_attempts=8,
)

request_account_limiter = AuthenticationRateLimiter(
    window_seconds=15 * 60,
    max_attempts=4,
)

complete_ip_limiter = AuthenticationRateLimiter(
    window_seconds=15 * 60,
    max_attempts=12,
)


def request_ip(
    request: Request,
) -> str | None:
    if request.client is None:
        return None

    return request.client.host


def bounded_user_agent(
    request: Request,
) -> str | None:
    value = request.headers.get("user-agent")

    if value is None:
        return None

    return value.replace("\r", " ").replace("\n", " ")[:1000]


def rate_limit_or_reject(
    limiter: AuthenticationRateLimiter,
    *,
    key: str,
) -> None:
    decision = limiter.check_and_record(key)

    if decision.allowed:
        return

    raise HTTPException(
        status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
        detail=("Too many account recovery attempts. Try again later."),
        headers={"Retry-After": str(decision.retry_after_seconds)},
    )


@router.post(
    "/password-reset/request",
    response_model=(PasswordResetResponse),
)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
) -> PasswordResetResponse:
    ip = request_ip(request) or "unknown"

    account_identifier = privacy_safe_identifier(payload.email)

    rate_limit_or_reject(
        request_ip_limiter,
        key=f"password-reset-ip:{ip}",
    )

    rate_limit_or_reject(
        request_account_limiter,
        key=(f"password-reset-account:{account_identifier}"),
    )

    settings = get_email_runtime_settings()

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.email == payload.email,
                User.status == UserStatus.active,
            )
        )

        if user is not None:
            issue_password_reset(
                db,
                user=user,
                settings=settings,
                requested_ip_address=(request_ip(request)),
                requested_user_agent=(bounded_user_agent(request)),
            )
        else:
            record_audit_event(
                db,
                action=("authentication.password_reset_requested"),
                entity_type="user",
                metadata={"account_identifier": (account_identifier)},
                ip_address=(request_ip(request)),
                user_agent=(bounded_user_agent(request)),
            )

        db.commit()

    return PasswordResetResponse(message=GENERIC_RESET_MESSAGE)


@router.post(
    "/password-reset/complete",
    response_model=(PasswordResetResponse),
)
def reset_password(
    payload: (PasswordResetCompleteRequest),
    request: Request,
) -> PasswordResetResponse:
    ip = request_ip(request) or "unknown"

    rate_limit_or_reject(
        complete_ip_limiter,
        key=(f"password-reset-complete:{ip}"),
    )

    with SessionLocal() as db:
        completed = complete_password_reset(
            db,
            raw_token=payload.token,
            new_password=(payload.password),
            request_ip_address=(request_ip(request)),
            request_user_agent=(bounded_user_agent(request)),
        )

        if not completed:
            db.rollback()

            raise HTTPException(
                status_code=(status.HTTP_400_BAD_REQUEST),
                detail=("This password reset link is invalid or has expired."),
            )

        db.commit()

    return PasswordResetResponse(message=("Password updated. Please sign in again."))

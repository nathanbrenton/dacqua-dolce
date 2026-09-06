import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.privacy import (
    privacy_safe_identifier,
)
from app.db.session import SessionLocal
from app.models.catalog import Product
from app.models.identity import (
    User,
    UserSession,
    UserStatus,
)
from app.models.quote import QuoteRequest
from app.schemas.quote import (
    QuoteRequestCreate,
    QuoteRequestRead,
)
from app.services.audit import (
    record_audit_event,
)
from app.services.auth_rate_limit import (
    AuthenticationRateLimiter,
)
from app.services.sessions import (
    hash_session_token,
)

router = APIRouter(
    prefix="/quotes",
    tags=["quotes"],
)

settings = get_settings()

quote_limiter = AuthenticationRateLimiter(
    window_seconds=15 * 60,
    max_attempts=8,
)


def request_ip(
    request: Request,
) -> str | None:
    if request.client is None:
        return None

    return request.client.host


def optional_user(
    request: Request,
) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)

    if token is None:
        return None

    with SessionLocal() as db:
        session_record = db.scalar(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                UserSession.token_hash == hash_session_token(token),
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )

        if session_record is None or session_record.user.status != UserStatus.active:
            return None

        db.expunge(session_record.user)

        return session_record.user


@router.post(
    "",
    response_model=QuoteRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_quote_request(
    payload: QuoteRequestCreate,
    request: Request,
) -> QuoteRequestRead:
    ip = request_ip(request) or "unknown"

    decision = quote_limiter.check_and_record(f"quote:{ip}")

    if not decision.allowed:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Too many quote requests. Try again later."),
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    product_uuid: uuid.UUID | None = None

    if payload.product_id is not None:
        try:
            product_uuid = uuid.UUID(payload.product_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                detail=("Invalid product identifier."),
            ) from exc

    current_user = optional_user(request)

    with SessionLocal() as db:
        if product_uuid is not None:
            product = db.scalar(
                select(Product).where(
                    Product.id == product_uuid,
                    Product.active.is_(True),
                )
            )

            if product is None:
                raise HTTPException(
                    status_code=(status.HTTP_404_NOT_FOUND),
                    detail=("System not found."),
                )

        quote = QuoteRequest(
            product_id=product_uuid,
            user_id=(current_user.id if current_user is not None else None),
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            message=payload.message,
        )

        db.add(quote)
        db.flush()

        record_audit_event(
            db,
            action="quote.requested",
            entity_type="quote_request",
            entity_id=str(quote.id),
            actor_user_id=(current_user.id if current_user is not None else None),
            metadata={
                "product_id": (str(product_uuid) if product_uuid is not None else None),
                "account_identifier": (privacy_safe_identifier(payload.email)),
            },
            ip_address=request_ip(request),
            user_agent=(request.headers.get("user-agent")),
        )

        db.commit()

        return QuoteRequestRead(
            id=str(quote.id),
            status=quote.status.value,
        )

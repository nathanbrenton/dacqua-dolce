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
from app.core.email_config import (
    get_email_runtime_settings,
)
from app.core.privacy import (
    privacy_safe_identifier,
)
from app.db.session import SessionLocal
from app.integrations.email import (
    EmailMessage,
)
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
from app.services.email_delivery import (
    deliver_email,
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


def send_quote_emails(
    *,
    db: object,
    quote: QuoteRequest,
    product: Product | None,
) -> None:
    email_settings = get_email_runtime_settings()

    product_label = product.name if product is not None else "General consultation"

    deliver_email(
        db,
        settings=email_settings,
        message=EmailMessage(
            sender=(email_settings.email_from),
            recipient=quote.email,
            subject=("We received your D'Acqua Dolce request"),
            body_text=(
                "Thank you for contacting "
                "D'Acqua Dolce.\n\n"
                "Your request has been "
                "received.\n"
                f"Reference: {quote.id}\n"
                f"System: {product_label}\n\n"
                "A team member can follow "
                "up using the contact "
                "information you provided."
            ),
        ),
        category=("quote_customer_receipt"),
        related_entity_type=("quote_request"),
        related_entity_id=str(quote.id),
    )

    operator_to = email_settings.email_operator_to

    if operator_to is None:
        return

    message_lines = [
        "New D'Acqua Dolce quote request",
        "",
        f"Reference: {quote.id}",
        f"System: {product_label}",
        f"Name: {quote.name}",
        f"Email: {quote.email}",
    ]

    if quote.phone:
        message_lines.append(f"Phone: {quote.phone}")

    if quote.message:
        message_lines.extend(
            [
                "",
                "Customer message:",
                quote.message,
            ]
        )

    deliver_email(
        db,
        settings=email_settings,
        message=EmailMessage(
            sender=(email_settings.email_from),
            recipient=operator_to,
            subject=("New D'Acqua Dolce quote request"),
            body_text="\n".join(message_lines),
        ),
        category=("quote_operator_notification"),
        related_entity_type=("quote_request"),
        related_entity_id=str(quote.id),
    )


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
        product: Product | None = None

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
            entity_type=("quote_request"),
            entity_id=str(quote.id),
            actor_user_id=(current_user.id if current_user is not None else None),
            metadata={
                "product_id": (str(product_uuid) if product_uuid is not None else None),
                "account_identifier": (privacy_safe_identifier(payload.email)),
            },
            ip_address=request_ip(request),
            user_agent=(request.headers.get("user-agent")),
        )

        send_quote_emails(
            db=db,
            quote=quote,
            product=product,
        )

        db.commit()

        return QuoteRequestRead(
            id=str(quote.id),
            status=quote.status.value,
        )

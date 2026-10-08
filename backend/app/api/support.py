import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.privacy import privacy_safe_identifier
from app.db.session import SessionLocal
from app.models.catalog import Product
from app.models.communications import (
    CommunicationDirection,
    CommunicationEvent,
    CommunicationMessage,
    CommunicationMessageStatus,
    CommunicationThread,
    CommunicationThreadStatus,
)
from app.models.identity import User, UserSession, UserStatus
from app.schemas.support import SupportRequestCreate, SupportRequestRead
from app.services.audit import record_audit_event
from app.services.auth_rate_limit import AuthenticationRateLimiter
from app.services.sessions import hash_session_token
from app.services.turnstile import verify_public_form_turnstile

router = APIRouter(prefix="/support", tags=["support"])
settings = get_settings()

support_limiter = AuthenticationRateLimiter(
    window_seconds=15 * 60,
    max_attempts=8,
)


def request_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def optional_user(request: Request) -> User | None:
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


def support_request_is_trapped(payload: SupportRequestCreate) -> bool:
    """Detect the intentionally empty public-form honeypot field."""
    return payload.website is not None


def support_subject(
    kind: str,
    *,
    product_name: str | None,
) -> str:
    labels = {
        "warranty": "Warranty support",
        "product_support": "Product support",
        "general_support": "General support",
    }
    base = labels[kind]
    return f"{base} — {product_name}" if product_name is not None else base


@router.post(
    "",
    response_model=SupportRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_support_request(
    payload: SupportRequestCreate,
    request: Request,
) -> SupportRequestRead:
    ip = request_ip(request) or "unknown"
    rate = support_limiter.check_and_record(f"support:{ip}")
    if not rate.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many support requests. Try again later.",
            headers={"Retry-After": str(rate.retry_after_seconds)},
        )

    if support_request_is_trapped(payload):
        # Deliberately return the normal success shape without creating a
        # customer communication. This avoids teaching simple form bots which
        # field triggered the rejection while keeping spam out of Operations.
        return SupportRequestRead(
            id=str(uuid.uuid4()),
            message=(
                "Your support request was received. "
                "Our team can continue the conversation using the contact information "
                "you provided."
            ),
        )

    verify_public_form_turnstile(request, action="support")

    current_user = optional_user(request)
    if current_user is not None and payload.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Signed-in support requests must use the account email address.",
        )

    product_uuid: uuid.UUID | None = None
    if payload.product_id is not None:
        try:
            product_uuid = uuid.UUID(payload.product_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid product identifier.",
            ) from exc

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
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="System not found.",
                )

        now = datetime.now(UTC)
        subject = support_subject(
            payload.kind,
            product_name=(product.name if product is not None else None),
        )
        thread = CommunicationThread(
            customer_user_id=(current_user.id if current_user is not None else None),
            subject=subject,
            related_entity_type="support_request",
            status=CommunicationThreadStatus.open,
            last_message_at=now,
        )
        db.add(thread)
        db.flush()
        thread.related_entity_id = str(thread.id)

        message = CommunicationMessage(
            thread_id=thread.id,
            direction=CommunicationDirection.inbound,
            status=CommunicationMessageStatus.received,
            provider="web",
            sender_address=payload.email,
            sender_name=payload.name,
            subject=subject,
            body_text=payload.message,
            content_redacted=False,
            received_at=now,
            created_at=now,
        )
        db.add(message)
        db.flush()

        db.add(
            CommunicationEvent(
                message_id=message.id,
                provider="web",
                event_type="support_request_submitted",
                provider_event_id=f"support:{message.id}",
                occurred_at=now,
                details={
                    "kind": payload.kind,
                    "name": payload.name,
                    "email": payload.email,
                    "phone": payload.phone,
                    "product_id": str(product.id) if product is not None else None,
                    "product_name": product.name if product is not None else None,
                },
            )
        )

        record_audit_event(
            db,
            action="support.requested",
            entity_type="communication_thread",
            entity_id=str(thread.id),
            actor_user_id=(current_user.id if current_user is not None else None),
            metadata={
                "kind": payload.kind,
                "product_id": str(product.id) if product is not None else None,
                "account_identifier": privacy_safe_identifier(payload.email),
            },
            ip_address=request_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()

        return SupportRequestRead(
            id=str(thread.id),
            message=(
                "Your support request was received. "
                "Our team can continue the conversation using the contact information "
                "you provided."
            ),
        )

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
from app.core.contact_method import contact_method_label
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
from app.models.catalog import Product, ProductInventory
from app.models.identity import (
    User,
    UserSession,
    UserStatus,
)
from app.models.quote import QuoteRequest
from app.schemas.quote import (
    QuoteRequestCreate,
    QuoteRequestRead,
    RecommendationContext,
    RecommendationDecision,
)
from app.services.audit import (
    record_audit_event,
)
from app.services.auth_rate_limit import (
    AuthenticationRateLimiter,
)
from app.services.commerce import active_reserved_quantity
from app.services.email_delivery import (
    deliver_email,
)
from app.services.product_configuration import configuration_inquiry_text
from app.services.public_availability import resolve_public_availability
from app.services.quote_acknowledgements import deliver_quote_acknowledgement
from app.services.recommendations import (
    RECOMMENDATION_POLICY_VERSION,
    evaluate_recommendation,
)
from app.services.sessions import (
    hash_session_token,
)
from app.services.turnstile import verify_public_form_turnstile

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

    # The sender already names D'Acqua Dolce, so the subject doesn't repeat it.
    # The customer's name keeps each alert distinct (mail apps otherwise stack
    # identical subjects into one thread and treat them as bulk mail).
    inquiry_label = (
        "New expert inquiry"
        if quote.inquiry_context == "expert_inquiry"
        else "New product inquiry"
        if quote.inquiry_context == "product_inquiry"
        else "New recommendation inquiry"
        if quote.inquiry_context == "recommendation_inquiry"
        else "New quote request"
    )
    customer_name = " ".join(str(quote.name or "").split())[:120]
    subject = (
        f"{inquiry_label} — {customer_name}" if customer_name else inquiry_label
    )

    deliver_quote_acknowledgement(
        db,
        settings=email_settings,
        quote_id=str(quote.id),
        recipient=quote.email,
        customer_user_id=quote.user_id,
    )

    operator_recipients = email_settings.operator_recipients

    if not operator_recipients:
        return

    # Kept short on purpose: contact details, product family and the
    # customer's message. Everything else is in Operations > Requests.
    product_family = (
        "None chosen"
        if product is None
        else product.product_family or product.name
    )
    message_lines = [
        f"Name: {quote.name}",
        f"Email: {quote.email}",
        f"Phone: {quote.phone or 'Not given'}",
        f"Prefers: {contact_method_label(quote.preferred_contact_method) or 'Not given'}",
        f"Product family: {product_family}",
        "",
        "Message:",
        quote.message or "(No message)",
        "",
        "Full details are in Operations > Requests.",
    ]

    # One message per staff inbox: recipients don't see each other's
    # addresses, and each delivery succeeds or fails on its own record.
    for operator_to in operator_recipients:
        deliver_email(
            db,
            settings=email_settings,
            message=EmailMessage(
                sender=(email_settings.email_from),
                recipient=operator_to,
                subject=subject,
                body_text="\n".join(message_lines),
            ),
            category=("quote_operator_notification"),
            related_entity_type=("quote_request"),
            related_entity_id=str(quote.id),
        )




@router.post(
    "/recommendation",
    response_model=RecommendationDecision,
)
def get_recommendation(
    payload: RecommendationContext,
) -> RecommendationDecision:
    return evaluate_recommendation(payload)


def resolve_inquiry_context(
    *,
    product_id: str | None,
    recommendation_context: object | None,
    inquiry_context: str,
) -> str:
    """Classify declared inquiry origin while rejecting incompatible product data.

    Origin is display/audit metadata, not an authorization credential.
    Water-property answers are permitted in expert consultations.
    """
    if product_id is not None:
        allowed = {"legacy_quote_request", "product_inquiry"}
        inferred = "product_inquiry"
    elif recommendation_context is not None:
        allowed = {
            "legacy_quote_request",
            "expert_inquiry",
            "recommendation_inquiry",
        }
        inferred = (
            "expert_inquiry"
            if inquiry_context == "expert_inquiry"
            else "recommendation_inquiry"
        )
    else:
        allowed = {"legacy_quote_request", "expert_inquiry"}
        inferred = "expert_inquiry"

    if inquiry_context not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Inquiry context does not match the request.",
        )
    return inferred if inquiry_context != "legacy_quote_request" else "legacy_quote_request"


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

    verify_public_form_turnstile(request, action="quote")

    product_uuid: uuid.UUID | None = None

    if payload.product_id is not None:
        try:
            product_uuid = uuid.UUID(payload.product_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
                detail=("Invalid product identifier."),
            ) from exc

    inquiry_context = resolve_inquiry_context(
        product_id=payload.product_id,
        recommendation_context=payload.recommendation_context,
        inquiry_context=payload.inquiry_context,
    )

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

            inventory = db.scalar(
                select(ProductInventory)
                .where(
                    ProductInventory.product_id == product.id,
                    ProductInventory.variant_id.is_(None),
                )
                .order_by(ProductInventory.updated_at.desc())
            )
            reserved_quantity = (
                active_reserved_quantity(
                    db,
                    product_id=product.id,
                    variant_id=None,
                )
                if inventory is not None
                else 0
            )
            availability = resolve_public_availability(
                inventory,
                reserved_quantity=reserved_quantity,
                online_sale_approved=product.online_sale_approved,
                lifecycle_status=product.lifecycle_status,
                allow_inquiry_when_unavailable=product.allow_inquiry_when_unavailable,
            )
            if (
                availability.status in {"out_of_stock", "discontinued"}
                and not availability.can_inquire
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Customer inquiries are disabled for this product while unavailable.",
                )

        if payload.configuration is not None:
            if product is None or payload.configuration.sku != product.sku:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Configured system must match the selected catalog product.",
                )
            if inquiry_context != "product_inquiry":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Product configuration requires a product inquiry.",
                )

        # The request's product/option IDs are never used as a price authority.
        # Canonical server-rendered notes let existing staff and email workflows
        # see the selection without a schema migration or parallel pricing API.
        configured_message = payload.message
        if payload.configuration is not None:
            summary = configuration_inquiry_text(payload.configuration)
            configured_message = "\n\n".join(
                section for section in [summary, payload.message] if section
            )
            if len(configured_message) > 4000:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Configuration and message exceed the 4000-character limit.",
                )

        recommendation_decision = (
            evaluate_recommendation(payload.recommendation_context)
            if payload.recommendation_context is not None
            else None
        )

        quote = QuoteRequest(
            inquiry_context=inquiry_context,
            product_id=product_uuid,
            user_id=(current_user.id if current_user is not None else None),
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            preferred_contact_method=payload.preferred_contact_method,
            message=configured_message,
            recommendation_context=(
                payload.recommendation_context.model_dump(mode="json")
                if payload.recommendation_context is not None
                else None
            ),
            recommendation_decision=(
                recommendation_decision.model_dump(mode="json")
                if recommendation_decision is not None
                else None
            ),
            recommendation_policy_version=(
                RECOMMENDATION_POLICY_VERSION
                if recommendation_decision is not None
                else None
            ),
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
                "inquiry_context": inquiry_context,
                "structured_configuration_submitted": payload.configuration is not None,
                "product_id": (str(product_uuid) if product_uuid is not None else None),
                "account_identifier": (privacy_safe_identifier(payload.email)),
                "recommendation_decision_code": (
                    recommendation_decision.code
                    if recommendation_decision is not None
                    else None
                ),
                "recommendation_human_review": (
                    recommendation_decision.human_review
                    if recommendation_decision is not None
                    else None
                ),
                "recommendation_requires_third_party_lab": (
                    recommendation_decision.requires_third_party_lab
                    if recommendation_decision is not None
                    else None
                ),
                "recommendation_policy_version": (
                    RECOMMENDATION_POLICY_VERSION
                    if recommendation_decision is not None
                    else None
                ),
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

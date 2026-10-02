import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import String, cast, func, not_, or_, select
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import CurrentUser, DatabaseSession
from app.core.email import normalize_email_address
from app.core.email_config import get_email_runtime_settings
from app.models.audit import AuditEvent
from app.models.catalog import (
    Product,
    ProductDocumentType,
    ProductInventory,
    ProductPrice,
    ProductRelationship,
    ProductVariant,
)
from app.models.commerce import (
    Order,
    OrderCancellationRequest,
    OrderCharge,
    OrderItem,
    OrderShipment,
)
from app.models.communications import (
    CommunicationAttachment,
    CommunicationMessage,
    CommunicationRecipient,
    CommunicationThread,
)
from app.models.customer import (
    CustomerAddress,
    CustomerEquipment,
    CustomerProfile,
)
from app.models.email import EmailDelivery, EmailDeliveryStatus
from app.models.identity import (
    RoleName,
    User,
    UserRole,
)
from app.models.quote import (
    FormalQuote,
    QuoteRequest,
    QuoteRequestStatus,
)
from app.schemas.operations import (
    CustomerEquipmentCreateRequest,
    CustomerEquipmentUpdateRequest,
    FormalQuoteCreate,
    InventoryUpdateRequest,
    OperationsAuditEventPageRead,
    OperationsAuditEventRead,
    OperationsCommunicationAttachmentRead,
    OperationsCommunicationMessageRead,
    OperationsCommunicationOriginatingRequestRead,
    OperationsCommunicationRead,
    OperationsCommunicationRecipientRead,
    OperationsCommunicationReplyCreate,
    OperationsCommunicationReplyRead,
    OperationsCommunicationThreadDetailRead,
    OperationsCommunicationThreadRead,
    OperationsCommunicationThreadStatusUpdate,
    OperationsCustomerAddressRead,
    OperationsCustomerEquipmentRead,
    OperationsCustomerRead,
    OperationsFormalQuoteItemRead,
    OperationsFormalQuoteRead,
    OperationsInsightBucketRead,
    OperationsInventoryRead,
    OperationsOrderCancellationRead,
    OperationsOrderCustomerRead,
    OperationsOrderItemRead,
    OperationsOrderRead,
    OperationsOrderShipmentRead,
    OperationsPricingRead,
    OperationsProductRead,
    OperationsProductRelationshipRead,
    OperationsProductVariantRead,
    OperationsQuoteRead,
    OperationsSalesInsightsRead,
    OperationsSummaryRead,
    OrderCancellationReviewUpdate,
    OrderFulfillmentUpdate,
    PricingUpdateRequest,
    ProductRelationshipCreateRequest,
    ProductRelationshipUpdateRequest,
    QuoteNotesUpdate,
    QuoteStatusUpdate,
)
from app.services.audit import record_audit_event
from app.services.cancellations import (
    CancellationError,
    cancellation_mode_for_order,
    get_order_cancellation_request,
    review_order_cancellation,
)
from app.services.commerce import (
    active_reserved_quantity,
)
from app.services.communications_reply import (
    CommunicationReplyConfigurationError,
    CommunicationReplyRecipientUnavailable,
    CommunicationReplySenderNotAllowed,
    resolve_communication_reply_sender_options,
    resolve_communication_reply_target_details,
    send_communication_reply,
)
from app.services.formal_quotes import (
    FormalQuoteChargeInput,
    FormalQuoteLineInput,
    create_formal_quote_revision,
    present_formal_quote,
)
from app.services.fulfillment import (
    FulfillmentError,
    transition_order_fulfillment,
)
from app.services.inventory_observations import (
    InventoryObservation,
    apply_inventory_observation,
)
from app.services.operations_access import (
    require_audit_log_read,
    require_customer_equipment_write,
    require_operations,
    require_pricing_inventory_write,
)
from app.services.pricing import select_effective_price
from app.services.sales_insights import summarize_assisted_sales

router = APIRouter(prefix="/operations", tags=["operations"])


def product_name_for_quote(
    db: DatabaseSession,
    product_id: uuid.UUID | None,
) -> str | None:
    if product_id is None:
        return None

    return db.scalar(select(Product.name).where(Product.id == product_id))


def operations_formal_quote_read(
    formal_quote: FormalQuote,
) -> OperationsFormalQuoteRead:
    return OperationsFormalQuoteRead(
        id=str(formal_quote.id),
        revision_number=formal_quote.revision_number,
        status=formal_quote.status.value,
        customer_user_id=(
            str(formal_quote.customer_user_id)
            if formal_quote.customer_user_id is not None
            else None
        ),
        authored_by_user_id=(
            str(formal_quote.authored_by_user_id)
            if formal_quote.authored_by_user_id is not None
            else None
        ),
        currency=formal_quote.currency,
        subtotal_amount_minor=formal_quote.subtotal_amount_minor,
        charges_amount_minor=formal_quote.charges_amount_minor,
        total_amount_minor=formal_quote.total_amount_minor,
        delivery_address=formal_quote.delivery_address_snapshot,
        billing_address=formal_quote.billing_address_snapshot,
        charges=[
            {
                "kind": charge.kind,
                "label": charge.label,
                "amount_minor": charge.amount_minor,
            }
            for charge in formal_quote.charges
        ],
        warranty_snapshots=[
            {
                "id": str(snapshot.id),
                "sku": snapshot.sku_snapshot,
                "product_name": snapshot.product_name_snapshot,
                "manufacturer_name": snapshot.manufacturer_name_snapshot,
                "title": snapshot.title_snapshot,
                "version": snapshot.version_snapshot,
                "path": snapshot.storage_path_snapshot,
                "content_type": snapshot.content_type_snapshot,
                "checksum_sha256": snapshot.checksum_sha256_snapshot,
                "source_reference": snapshot.source_reference_snapshot,
                "verified_at": snapshot.verified_at_snapshot.isoformat(),
            }
            for snapshot in formal_quote.warranty_snapshots
        ],
        policy_snapshots=[
            {
                "id": snapshot.id,
                "kind": snapshot.kind,
                "version": snapshot.version_snapshot,
                "title": snapshot.title_snapshot,
                "body": snapshot.body_snapshot,
                "refund_terms": (
                    snapshot.structured_terms_snapshot
                    if snapshot.kind.value == "refund"
                    else None
                ),
                "content_sha256": snapshot.content_sha256,
                "structured_terms_sha256": snapshot.structured_terms_sha256,
                "effective_at": snapshot.effective_at_snapshot,
            }
            for snapshot in formal_quote.policy_snapshots
        ],
        customer_note=formal_quote.customer_note,
        presented_at=(
            formal_quote.presented_at.isoformat()
            if formal_quote.presented_at is not None
            else None
        ),
        expires_at=(
            formal_quote.expires_at.isoformat()
            if formal_quote.expires_at is not None
            else None
        ),
        approved_at=(
            formal_quote.approved_at.isoformat()
            if formal_quote.approved_at is not None
            else None
        ),
        created_at=formal_quote.created_at.isoformat(),
        items=[
            OperationsFormalQuoteItemRead(
                id=str(item.id),
                product_id=(
                    str(item.product_id)
                    if item.product_id is not None
                    else None
                ),
                variant_id=(
                    str(item.variant_id)
                    if item.variant_id is not None
                    else None
                ),
                sku=item.sku_snapshot,
                name=item.name_snapshot,
                quantity=item.quantity,
                unit_amount_minor=item.unit_amount_minor,
                line_total_minor=item.line_total_minor,
                currency=item.currency,
                pricing_policy_mode=item.pricing_policy_mode_snapshot,
                estimated_lead_time=item.estimated_lead_time_snapshot,
            )
            for item in formal_quote.items
        ],
    )


def operations_quote_read(
    db: DatabaseSession,
    *,
    quote: QuoteRequest,
) -> OperationsQuoteRead:
    return OperationsQuoteRead(
        id=str(quote.id),
        product_id=(
            str(quote.product_id)
            if quote.product_id is not None
            else None
        ),
        product_name=product_name_for_quote(
            db,
            quote.product_id,
        ),
        name=quote.name,
        email=quote.email,
        phone=quote.phone,
        message=quote.message,
        recommendation_context=getattr(
            quote,
            "recommendation_context",
            None,
        ),
        recommendation_decision=getattr(
            quote,
            "recommendation_decision",
            None,
        ),
        recommendation_policy_version=getattr(
            quote,
            "recommendation_policy_version",
            None,
        ),
        internal_notes=quote.internal_notes,
        status=quote.status.value,
        created_at=quote.created_at.isoformat(),
        formal_quotes=[
            operations_formal_quote_read(formal_quote)
            for formal_quote in getattr(quote, "formal_quotes", [])
        ],
    )


@router.get("/summary", response_model=OperationsSummaryRead)
def operations_summary(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsSummaryRead:
    require_operations(db, user=current_user)

    new_quotes = (
        db.scalar(
            select(func.count())
            .select_from(QuoteRequest)
            .where(QuoteRequest.status == QuoteRequestStatus.new)
        )
        or 0
    )

    open_quotes = (
        db.scalar(
            select(func.count())
            .select_from(QuoteRequest)
            .where(
                QuoteRequest.status.in_(
                    (
                        QuoteRequestStatus.new,
                        QuoteRequestStatus.contacted,
                        QuoteRequestStatus.quoted,
                    )
                )
            )
        )
        or 0
    )

    open_recommendation_decisions = db.scalars(
        select(QuoteRequest.recommendation_decision).where(
            QuoteRequest.status.in_(
                (
                    QuoteRequestStatus.new,
                    QuoteRequestStatus.contacted,
                    QuoteRequestStatus.quoted,
                )
            ),
            QuoteRequest.recommendation_decision.is_not(None),
        )
    ).all()

    recommendation_human_review = sum(
        1
        for decision in open_recommendation_decisions
        if isinstance(decision, dict) and decision.get("human_review") is True
    )
    recommendation_lab_testing = sum(
        1
        for decision in open_recommendation_decisions
        if (
            isinstance(decision, dict)
            and decision.get("requires_third_party_lab") is True
        )
    )

    active_products = (
        db.scalar(select(func.count()).select_from(Product).where(Product.active.is_(True))) or 0
    )

    failed_email_deliveries = (
        db.scalar(
            select(func.count())
            .select_from(EmailDelivery)
            .where(EmailDelivery.status == EmailDeliveryStatus.failed)
        )
        or 0
    )

    return OperationsSummaryRead(
        new_quotes=int(new_quotes),
        open_quotes=int(open_quotes),
        recommendation_human_review=recommendation_human_review,
        recommendation_lab_testing=recommendation_lab_testing,
        active_products=int(active_products),
        failed_email_deliveries=int(failed_email_deliveries),
    )


@router.get(
    "/sales-insights",
    response_model=OperationsSalesInsightsRead,
)
def operations_sales_insights(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsSalesInsightsRead:
    require_operations(db, user=current_user)

    rows = db.execute(
        select(
            QuoteRequest.recommendation_context,
            QuoteRequest.recommendation_decision,
        ).order_by(QuoteRequest.created_at)
    ).all()
    insights = summarize_assisted_sales(rows)

    def buckets(values):
        return [
            OperationsInsightBucketRead(
                value=item.value,
                count=item.count,
            )
            for item in values
        ]

    return OperationsSalesInsightsRead(
        total_requests=insights.total_requests,
        structured_requests=insights.structured_requests,
        source_water=buckets(insights.source_water),
        treatment_preference=buckets(insights.treatment_preference),
        service_postal_codes=buckets(insights.service_postal_codes),
        limited_utility_requests=insights.limited_utility_requests,
        lab_required_requests=insights.lab_required_requests,
        known_hardness_requests=insights.known_hardness_requests,
        research_network_yes=insights.research_network_yes,
    )


def audit_metadata_text(
    event: AuditEvent,
    key: str,
) -> str | None:
    value = (event.metadata_json or {}).get(key)

    if not isinstance(value, str):
        return None

    stripped = value.strip()
    return stripped or None


def audit_event_outcome(
    event: AuditEvent,
) -> str:
    explicit = audit_metadata_text(
        event,
        "outcome",
    )

    if explicit in {"succeeded", "failed"}:
        return explicit

    return (
        "failed"
        if event.action.endswith(".failed")
        else "succeeded"
    )


def operations_audit_event_read(
    *,
    event: AuditEvent,
    actor_email: str | None = None,
) -> OperationsAuditEventRead:
    return OperationsAuditEventRead(
        id=str(event.id),
        actor_user_id=(
            str(event.actor_user_id)
            if event.actor_user_id is not None
            else None
        ),
        actor_email=actor_email,
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        environment=event.environment,
        outcome=audit_event_outcome(event),
        request_id=audit_metadata_text(
            event,
            "request_id",
        ),
        error_category=audit_metadata_text(
            event,
            "error_category",
        ),
        endpoint=audit_metadata_text(
            event,
            "endpoint",
        ),
        error_code=audit_metadata_text(
            event,
            "error_code",
        ),
        created_at=event.created_at.isoformat(),
    )


def escaped_like(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


AuditOutcome = Literal["succeeded", "failed"]
AuditSort = Literal["newest", "oldest"]


@router.get(
    "/audit-events",
    response_model=OperationsAuditEventPageRead,
)
def list_audit_events(
    db: DatabaseSession,
    current_user: CurrentUser,
    from_at: Annotated[
        datetime | None,
        Query(alias="from"),
    ] = None,
    to_at: Annotated[
        datetime | None,
        Query(alias="to"),
    ] = None,
    actor: Annotated[
        str | None,
        Query(max_length=160),
    ] = None,
    outcome: AuditOutcome | None = None,
    action: Annotated[
        str | None,
        Query(max_length=120),
    ] = None,
    entity_type: Annotated[
        str | None,
        Query(max_length=120),
    ] = None,
    entity_id: Annotated[
        str | None,
        Query(max_length=120),
    ] = None,
    environment: Annotated[
        str | None,
        Query(max_length=40),
    ] = None,
    request_id: Annotated[
        str | None,
        Query(max_length=120),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=200),
    ] = None,
    sort: AuditSort = "newest",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[
        int,
        Query(ge=10, le=100),
    ] = 50,
) -> OperationsAuditEventPageRead:
    require_audit_log_read(
        db,
        user=current_user,
    )

    if (
        from_at is not None
        and to_at is not None
        and from_at > to_at
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Audit-log From time must be before "
                "the To time."
            ),
        )

    statement = (
        select(AuditEvent, User.email)
        .outerjoin(
            User,
            User.id == AuditEvent.actor_user_id,
        )
    )

    if from_at is not None:
        statement = statement.where(
            AuditEvent.created_at >= from_at
        )

    if to_at is not None:
        statement = statement.where(
            AuditEvent.created_at <= to_at
        )

    if actor:
        actor_pattern = (
            "%" + escaped_like(actor.strip()) + "%"
        )
        statement = statement.where(
            or_(
                User.email.ilike(
                    actor_pattern,
                    escape="\\",
                ),
                cast(
                    AuditEvent.actor_user_id,
                    String,
                ).ilike(
                    actor_pattern,
                    escape="\\",
                ),
            )
        )

    failed_expression = or_(
        AuditEvent.action.like("%.failed"),
        func.coalesce(
            AuditEvent.metadata_json[
                "outcome"
            ].astext,
            "",
        )
        == "failed",
    )

    if outcome == "failed":
        statement = statement.where(
            failed_expression
        )
    elif outcome == "succeeded":
        statement = statement.where(
            not_(failed_expression)
        )

    if action:
        statement = statement.where(
            AuditEvent.action == action.strip()
        )

    if entity_type:
        statement = statement.where(
            AuditEvent.entity_type
            == entity_type.strip()
        )

    if entity_id:
        entity_pattern = (
            "%"
            + escaped_like(entity_id.strip())
            + "%"
        )
        statement = statement.where(
            func.coalesce(
                AuditEvent.entity_id,
                "",
            ).ilike(
                entity_pattern,
                escape="\\",
            )
        )

    if environment:
        statement = statement.where(
            AuditEvent.environment
            == environment.strip()
        )

    if request_id:
        request_pattern = (
            "%"
            + escaped_like(request_id.strip())
            + "%"
        )
        statement = statement.where(
            func.coalesce(
                AuditEvent.metadata_json[
                    "request_id"
                ].astext,
                "",
            ).ilike(
                request_pattern,
                escape="\\",
            )
        )

    if search:
        search_pattern = (
            "%"
            + escaped_like(search.strip())
            + "%"
        )
        statement = statement.where(
            or_(
                cast(
                    AuditEvent.id,
                    String,
                ).ilike(
                    search_pattern,
                    escape="\\",
                ),
                User.email.ilike(
                    search_pattern,
                    escape="\\",
                ),
                AuditEvent.action.ilike(
                    search_pattern,
                    escape="\\",
                ),
                AuditEvent.entity_type.ilike(
                    search_pattern,
                    escape="\\",
                ),
                func.coalesce(
                    AuditEvent.entity_id,
                    "",
                ).ilike(
                    search_pattern,
                    escape="\\",
                ),
                AuditEvent.environment.ilike(
                    search_pattern,
                    escape="\\",
                ),
                func.coalesce(
                    AuditEvent.metadata_json[
                        "request_id"
                    ].astext,
                    "",
                ).ilike(
                    search_pattern,
                    escape="\\",
                ),
            )
        )

    ordering = (
        (
            AuditEvent.created_at.asc(),
            AuditEvent.id.asc(),
        )
        if sort == "oldest"
        else (
            AuditEvent.created_at.desc(),
            AuditEvent.id.desc(),
        )
    )

    rows = db.execute(
        statement.order_by(*ordering)
        .offset((page - 1) * page_size)
        .limit(page_size + 1)
    ).all()

    has_more = len(rows) > page_size
    visible_rows = rows[:page_size]

    return OperationsAuditEventPageRead(
        items=[
            operations_audit_event_read(
                event=event,
                actor_email=actor_email,
            )
            for event, actor_email in visible_rows
        ],
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


def operations_communication_read(
    *,
    delivery: EmailDelivery,
) -> OperationsCommunicationRead:
    return OperationsCommunicationRead(
        id=str(delivery.id),
        category=delivery.category,
        related_entity_type=(
            delivery.related_entity_type
        ),
        related_entity_id=(
            delivery.related_entity_id
        ),
        sender=delivery.sender,
        recipient=delivery.recipient,
        subject=delivery.subject,
        status=delivery.status.value,
        created_at=(
            delivery.created_at.isoformat()
        ),
        sent_at=(
            delivery.sent_at.isoformat()
            if delivery.sent_at is not None
            else None
        ),
    )


@router.get(
    "/communications",
    response_model=list[
        OperationsCommunicationRead
    ],
)
def list_communications(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsCommunicationRead]:
    require_operations(
        db,
        user=current_user,
    )

    deliveries = db.scalars(
        select(EmailDelivery)
        .order_by(
            EmailDelivery.created_at.desc(),
            EmailDelivery.id,
        )
        .limit(500)
    ).all()

    return [
        operations_communication_read(
            delivery=delivery,
        )
        for delivery in deliveries
    ]


def _communication_customer_emails(
    db: DatabaseSession,
    *,
    user_ids: set[uuid.UUID],
) -> dict[uuid.UUID, str]:
    if not user_ids:
        return {}

    rows = db.execute(
        select(
            User.id,
            User.email,
        ).where(User.id.in_(user_ids))
    ).all()

    return {
        user_id: email
        for user_id, email in rows
    }


SYSTEM_EMAIL_CATEGORIES = {
    "email_verification",
    "password_reset",
    "customer_welcome",
}


def _communication_thread_list_reads(
    db: DatabaseSession,
    *,
    threads: list[CommunicationThread],
) -> list[OperationsCommunicationThreadRead]:
    if not threads:
        return []

    thread_ids = [thread.id for thread in threads]
    customer_user_ids = {
        thread.customer_user_id
        for thread in threads
        if thread.customer_user_id is not None
    }
    customer_emails = _communication_customer_emails(
        db,
        user_ids=customer_user_ids,
    )

    messages = db.scalars(
        select(CommunicationMessage)
        .where(
            CommunicationMessage.thread_id.in_(thread_ids)
        )
        .order_by(
            CommunicationMessage.created_at,
            CommunicationMessage.id,
        )
    ).all()

    delivery_ids = {
        message.email_delivery_id
        for message in messages
        if message.email_delivery_id is not None
    }
    delivery_categories: dict[uuid.UUID, str] = {}
    if delivery_ids:
        deliveries = db.scalars(
            select(EmailDelivery).where(
                EmailDelivery.id.in_(delivery_ids)
            )
        ).all()
        delivery_categories = {
            delivery.id: delivery.category
            for delivery in deliveries
        }

    messages_by_thread: dict[
        uuid.UUID,
        list[CommunicationMessage],
    ] = {
        thread_id: []
        for thread_id in thread_ids
    }

    for message in messages:
        messages_by_thread[message.thread_id].append(message)

    response: list[OperationsCommunicationThreadRead] = []

    for thread in threads:
        thread_messages = messages_by_thread[thread.id]
        latest = (
            thread_messages[-1]
            if thread_messages
            else None
        )

        response.append(
            OperationsCommunicationThreadRead(
                id=str(thread.id),
                customer_user_id=(
                    str(thread.customer_user_id)
                    if thread.customer_user_id is not None
                    else None
                ),
                customer_email=(
                    customer_emails.get(thread.customer_user_id)
                    if thread.customer_user_id is not None
                    else None
                ),
                assigned_user_id=(
                    str(thread.assigned_user_id)
                    if thread.assigned_user_id is not None
                    else None
                ),
                subject=thread.subject,
                related_entity_type=thread.related_entity_type,
                related_entity_id=thread.related_entity_id,
                status=thread.status.value,
                last_message_at=(
                    thread.last_message_at.isoformat()
                    if thread.last_message_at is not None
                    else None
                ),
                created_at=thread.created_at.isoformat(),
                message_count=len(thread_messages),
                latest_direction=(
                    latest.direction.value
                    if latest is not None
                    else None
                ),
                latest_sender_address=(
                    latest.sender_address
                    if latest is not None
                    else None
                ),
                latest_subject=(
                    latest.subject
                    if latest is not None
                    else None
                ),
                failed_message_count=sum(
                    1
                    for message in thread_messages
                    if message.status.value == "failed"
                ),
                mailbox_kind=(
                    "system"
                    if any(
                        message.email_delivery_id is not None
                        and delivery_categories.get(
                            message.email_delivery_id
                        ) in SYSTEM_EMAIL_CATEGORIES
                        for message in thread_messages
                    )
                    else "inbox"
                ),
            )
        )

    return response


@router.get(
    "/communication-threads",
    response_model=list[
        OperationsCommunicationThreadRead
    ],
)
def list_communication_threads(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsCommunicationThreadRead]:
    require_operations(
        db,
        user=current_user,
    )

    threads = db.scalars(
        select(CommunicationThread)
        .order_by(
            CommunicationThread.last_message_at.desc().nullslast(),
            CommunicationThread.created_at.desc(),
            CommunicationThread.id,
        )
        .limit(200)
    ).all()

    return _communication_thread_list_reads(
        db,
        threads=list(threads),
    )


def _is_internal_postmark_inbound_address(
    address: str,
) -> bool:
    try:
        normalized = normalize_email_address(address)
    except ValueError:
        return False

    _, domain = normalized.rsplit("@", 1)
    return domain == "inbound.postmarkapp.com"


def _communication_message_reads(
    db: DatabaseSession,
    *,
    messages: list[CommunicationMessage],
) -> list[OperationsCommunicationMessageRead]:
    if not messages:
        return []

    message_ids = [message.id for message in messages]

    recipients = db.scalars(
        select(CommunicationRecipient)
        .where(
            CommunicationRecipient.message_id.in_(message_ids)
        )
        .order_by(
            CommunicationRecipient.message_id,
            CommunicationRecipient.recipient_type,
            CommunicationRecipient.position,
            CommunicationRecipient.id,
        )
    ).all()

    attachments = db.scalars(
        select(CommunicationAttachment)
        .where(
            CommunicationAttachment.message_id.in_(message_ids)
        )
        .order_by(
            CommunicationAttachment.message_id,
            CommunicationAttachment.created_at,
            CommunicationAttachment.id,
        )
    ).all()

    recipients_by_message: dict[
        uuid.UUID,
        list[CommunicationRecipient],
    ] = {
        message_id: []
        for message_id in message_ids
    }
    attachments_by_message: dict[
        uuid.UUID,
        list[CommunicationAttachment],
    ] = {
        message_id: []
        for message_id in message_ids
    }

    for recipient in recipients:
        recipients_by_message[recipient.message_id].append(recipient)

    for attachment in attachments:
        attachments_by_message[attachment.message_id].append(attachment)

    return [
        OperationsCommunicationMessageRead(
            id=str(message.id),
            direction=message.direction.value,
            status=message.status.value,
            author_user_id=(
                str(message.author_user_id)
                if message.author_user_id is not None
                else None
            ),
            sender_address=message.sender_address,
            sender_name=message.sender_name,
            subject=message.subject,
            body_text=message.body_text,
            content_redacted=message.content_redacted,
            sent_at=(
                message.sent_at.isoformat()
                if message.sent_at is not None
                else None
            ),
            received_at=(
                message.received_at.isoformat()
                if message.received_at is not None
                else None
            ),
            created_at=message.created_at.isoformat(),
            recipients=[
                OperationsCommunicationRecipientRead(
                    recipient_type=recipient.recipient_type.value,
                    address=recipient.address,
                    display_name=recipient.display_name,
                )
                for recipient in recipients_by_message[message.id]
                if not _is_internal_postmark_inbound_address(
                    recipient.address
                )
            ],
            attachments=[
                OperationsCommunicationAttachmentRead(
                    id=str(attachment.id),
                    filename=attachment.filename,
                    content_type=attachment.content_type,
                    size_bytes=attachment.size_bytes,
                    sha256=attachment.sha256,
                )
                for attachment in attachments_by_message[message.id]
            ],
        )
        for message in messages
    ]


def _communication_originating_request_read(
    db: DatabaseSession,
    *,
    thread: CommunicationThread,
) -> OperationsCommunicationOriginatingRequestRead | None:
    if (
        thread.related_entity_type != "quote_request"
        or thread.related_entity_id is None
    ):
        return None

    try:
        quote_id = uuid.UUID(thread.related_entity_id)
    except ValueError:
        return None

    quote = db.get(
        QuoteRequest,
        quote_id,
    )

    if quote is None:
        return None

    return OperationsCommunicationOriginatingRequestRead(
        request_type="website_quote_request",
        name=quote.name,
        email=quote.email,
        phone=quote.phone,
        product_name=product_name_for_quote(
            db,
            quote.product_id,
        ),
        message=quote.message,
        created_at=quote.created_at.isoformat(),
    )


@router.patch(
    "/communication-threads/{thread_id}",
    response_model=OperationsCommunicationThreadRead,
)
def update_communication_thread_status(
    thread_id: uuid.UUID,
    payload: OperationsCommunicationThreadStatusUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsCommunicationThreadRead:
    require_operations(
        db,
        user=current_user,
    )

    thread = db.get(
        CommunicationThread,
        thread_id,
    )

    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication thread not found.",
        )

    previous_status = thread.status
    thread.status = payload.status

    record_audit_event(
        db,
        action="communications.thread_status_changed",
        entity_type="communication_thread",
        entity_id=str(thread.id),
        actor_user_id=current_user.id,
        metadata={
            "previous_status": previous_status.value,
            "new_status": payload.status.value,
        },
    )

    db.commit()
    db.refresh(thread)

    return _communication_thread_list_reads(
        db,
        threads=[thread],
    )[0]


@router.get(
    "/communication-threads/{thread_id}",
    response_model=OperationsCommunicationThreadDetailRead,
)
def get_communication_thread(
    thread_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsCommunicationThreadDetailRead:
    require_operations(
        db,
        user=current_user,
    )

    thread = db.get(
        CommunicationThread,
        thread_id,
    )

    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication thread not found.",
        )

    summary = _communication_thread_list_reads(
        db,
        threads=[thread],
    )[0]

    messages = list(
        db.scalars(
            select(CommunicationMessage)
            .where(
                CommunicationMessage.thread_id == thread.id
            )
            .order_by(
                CommunicationMessage.created_at,
                CommunicationMessage.id,
            )
        ).all()
    )

    reply_target = resolve_communication_reply_target_details(
        db,
        thread=thread,
    )
    sender_options = resolve_communication_reply_sender_options(
        get_email_runtime_settings(),
        thread=thread,
    )

    return OperationsCommunicationThreadDetailRead(
        **summary.model_dump(),
        reply_target=reply_target.address,
        reply_target_source=reply_target.source,
        reply_sender_addresses=list(sender_options.addresses),
        reply_sender_default=sender_options.default,
        originating_request=_communication_originating_request_read(
            db,
            thread=thread,
        ),
        messages=_communication_message_reads(
            db,
            messages=messages,
        ),
    )


@router.post(
    "/communication-threads/{thread_id}/reply",
    response_model=OperationsCommunicationReplyRead,
    status_code=status.HTTP_201_CREATED,
)
def reply_to_communication_thread(
    thread_id: uuid.UUID,
    payload: OperationsCommunicationReplyCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsCommunicationReplyRead:
    require_operations(
        db,
        user=current_user,
    )

    thread = db.get(
        CommunicationThread,
        thread_id,
    )

    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Communication thread not found.",
        )

    try:
        result = send_communication_reply(
            db,
            settings=get_email_runtime_settings(),
            thread=thread,
            author_user_id=current_user.id,
            body_text=payload.body_text,
            recipient_override=payload.recipient,
            sender_override=payload.sender,
        )
    except CommunicationReplyRecipientUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except CommunicationReplySenderNotAllowed as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except CommunicationReplyConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    record_audit_event(
        db,
        action="communications.reply_attempted",
        entity_type="communication_thread",
        entity_id=str(thread.id),
        actor_user_id=current_user.id,
        metadata={
            "delivery_status": result.delivery.status.value,
            "provider": result.delivery.provider,
            "recipient": result.recipient,
            "recipients": list(result.recipients),
            "sender": result.sender,
        },
    )

    db.commit()
    db.refresh(thread)

    return OperationsCommunicationReplyRead(
        delivery_status=result.delivery.status.value,
        recipient=result.recipient,
        recipients=list(result.recipients),
        sender=result.sender,
        thread=get_communication_thread(
            thread.id,
            db,
            current_user,
        ),
    )


@router.get("/quotes", response_model=list[OperationsQuoteRead])
def list_quotes(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsQuoteRead]:
    require_operations(db, user=current_user)

    quotes = db.scalars(
        select(QuoteRequest)
        .options(
            selectinload(QuoteRequest.formal_quotes).selectinload(
                FormalQuote.items
            ),
            selectinload(QuoteRequest.formal_quotes).selectinload(
                FormalQuote.charges
            ),
            selectinload(QuoteRequest.formal_quotes).selectinload(
                FormalQuote.policy_snapshots
            ),
            selectinload(FormalQuote.warranty_snapshots),
        )
        .order_by(QuoteRequest.created_at.desc())
        .limit(200)
    ).all()

    return [
        operations_quote_read(
            db,
            quote=quote,
        )
        for quote in quotes
    ]


@router.patch("/quotes/{quote_id}", response_model=OperationsQuoteRead)
def update_quote_status(
    quote_id: uuid.UUID,
    payload: QuoteStatusUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsQuoteRead:
    require_operations(db, user=current_user)

    quote = db.get(QuoteRequest, quote_id)

    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote request not found.",
        )

    previous_status = quote.status
    quote.status = payload.status

    record_audit_event(
        db,
        action="quote.status_changed",
        entity_type="quote_request",
        entity_id=str(quote.id),
        actor_user_id=current_user.id,
        metadata={
            "previous_status": previous_status.value,
            "new_status": payload.status.value,
        },
    )

    db.commit()
    db.refresh(quote)

    return operations_quote_read(
        db,
        quote=quote,
    )


@router.put(
    "/quotes/{quote_id}/notes",
    response_model=OperationsQuoteRead,
)
def update_quote_notes(
    quote_id: uuid.UUID,
    payload: QuoteNotesUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsQuoteRead:
    require_operations(
        db,
        user=current_user,
    )

    quote = db.get(
        QuoteRequest,
        quote_id,
    )

    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote request not found.",
        )

    had_notes = quote.internal_notes is not None
    quote.internal_notes = payload.internal_notes

    record_audit_event(
        db,
        action="quote.notes_updated",
        entity_type="quote_request",
        entity_id=str(quote.id),
        actor_user_id=current_user.id,
        metadata={
            "had_notes": had_notes,
            "has_notes": (
                payload.internal_notes
                is not None
            ),
        },
    )

    db.commit()
    db.refresh(quote)

    return operations_quote_read(
        db,
        quote=quote,
    )


def operations_customer_read(
    db: DatabaseSession,
    *,
    user: User,
) -> OperationsCustomerRead:
    profile = db.get(
        CustomerProfile,
        user.id,
    )

    addresses = db.scalars(
        select(CustomerAddress)
        .where(
            CustomerAddress.user_id == user.id
        )
        .order_by(
            CustomerAddress.created_at,
            CustomerAddress.id,
        )
    ).all()

    equipment = db.scalars(
        select(CustomerEquipment)
        .where(CustomerEquipment.user_id == user.id)
        .order_by(
            CustomerEquipment.active.desc(),
            CustomerEquipment.installed_on.desc().nullslast(),
            CustomerEquipment.created_at.desc(),
        )
    ).all()

    return OperationsCustomerRead(
        id=str(user.id),
        email=user.email,
        status=user.status.value,
        first_name=(
            profile.first_name
            if profile is not None
            else None
        ),
        last_name=(
            profile.last_name
            if profile is not None
            else None
        ),
        phone=(
            profile.phone
            if profile is not None
            else None
        ),
        addresses=[
            OperationsCustomerAddressRead(
                id=str(address.id),
                label=address.label,
                line1=address.line1,
                line2=address.line2,
                city=address.city,
                region_code=address.region_code,
                postal_code=address.postal_code,
                country_code=address.country_code,
                is_default_shipping=(
                    address.is_default_shipping
                ),
                is_default_billing=(
                    address.is_default_billing
                ),
            )
            for address in addresses
        ],
        equipment=[
            OperationsCustomerEquipmentRead(
                id=str(item.id),
                product_id=str(item.product_id) if item.product_id is not None else None,
                variant_id=str(item.variant_id) if item.variant_id is not None else None,
                sku=item.sku_snapshot,
                product_name=item.name_snapshot,
                variant_name=item.variant_snapshot,
                serial_number=item.serial_number,
                location_label=item.location_label,
                installed_on=item.installed_on.isoformat() if item.installed_on else None,
                last_service_on=item.last_service_on.isoformat() if item.last_service_on else None,
                next_service_due_on=(
                    item.next_service_due_on.isoformat()
                    if item.next_service_due_on
                    else None
                ),
                active=item.active,
            )
            for item in equipment
        ],
        created_at=user.created_at.isoformat(),
    )


@router.get(
    "/customers",
    response_model=list[OperationsCustomerRead],
)
def list_customers(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsCustomerRead]:
    require_operations(
        db,
        user=current_user,
    )

    users = db.scalars(
        select(User)
        .join(
            UserRole,
            UserRole.user_id == User.id,
        )
        .where(
            UserRole.role == RoleName.customer
        )
        .order_by(
            User.created_at.desc(),
            User.email,
        )
        .limit(500)
    ).all()

    return [
        operations_customer_read(
            db,
            user=user,
        )
        for user in users
    ]


@router.post(
    "/customers/{customer_id}/equipment",
    response_model=OperationsCustomerRead,
)
def create_customer_equipment(
    customer_id: uuid.UUID,
    payload: CustomerEquipmentCreateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsCustomerRead:
    require_customer_equipment_write(db, user=current_user)
    customer = db.get(User, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account not found.",
        )
    customer_role = db.scalar(
        select(UserRole.id).where(
            UserRole.user_id == customer.id,
            UserRole.role == RoleName.customer,
        )
    )
    if customer_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account not found.",
        )
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    variant = None
    if payload.variant_id is not None:
        variant = db.get(ProductVariant, payload.variant_id)
        if variant is None or variant.product_id != product.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Variant does not belong to the selected product.",
            )

    equipment = CustomerEquipment(
        user_id=customer.id,
        product_id=product.id,
        variant_id=variant.id if variant is not None else None,
        sku_snapshot=variant.sku if variant is not None else product.sku,
        name_snapshot=product.name,
        variant_snapshot=variant.display_name if variant is not None else None,
        serial_number=payload.serial_number,
        location_label=payload.location_label,
        installed_on=payload.installed_on,
        last_service_on=payload.last_service_on,
        next_service_due_on=payload.next_service_due_on,
        active=True,
    )
    db.add(equipment)
    db.flush()
    record_audit_event(
        db,
        action="customer.equipment_recorded",
        entity_type="customer_equipment",
        entity_id=str(equipment.id),
        actor_user_id=current_user.id,
        metadata={"customer_id": str(customer.id), "product_id": str(product.id)},
    )
    db.commit()
    return operations_customer_read(db, user=customer)


@router.patch(
    "/customers/{customer_id}/equipment/{equipment_id}",
    response_model=OperationsCustomerRead,
)
def update_customer_equipment(
    customer_id: uuid.UUID,
    equipment_id: uuid.UUID,
    payload: CustomerEquipmentUpdateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsCustomerRead:
    require_customer_equipment_write(db, user=current_user)
    customer = db.get(User, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account not found.",
        )
    customer_role = db.scalar(
        select(UserRole.id).where(
            UserRole.user_id == customer.id,
            UserRole.role == RoleName.customer,
        )
    )
    if customer_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account not found.",
        )
    equipment = db.scalar(
        select(CustomerEquipment).where(
            CustomerEquipment.id == equipment_id,
            CustomerEquipment.user_id == customer.id,
        )
    )
    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment record not found.",
        )

    for field, value in payload.model_dump().items():
        setattr(equipment, field, value)
    record_audit_event(
        db,
        action="customer.equipment_updated",
        entity_type="customer_equipment",
        entity_id=str(equipment.id),
        actor_user_id=current_user.id,
        metadata={"customer_id": str(customer.id), "active": equipment.active},
    )
    db.commit()
    return operations_customer_read(db, user=customer)


def operations_cancellation_read(
    cancellation: OrderCancellationRequest,
) -> OperationsOrderCancellationRead:
    return OperationsOrderCancellationRead(
        id=str(cancellation.id),
        eligibility_mode=cancellation.eligibility_mode,
        status=cancellation.status,
        reason=cancellation.reason,
        review_note=cancellation.review_note,
        requested_at=cancellation.created_at.isoformat(),
        reviewed_at=(
            cancellation.reviewed_at.isoformat()
            if cancellation.reviewed_at is not None
            else None
        ),
        completed_at=(
            cancellation.completed_at.isoformat()
            if cancellation.completed_at is not None
            else None
        ),
    )


def operations_order_read(
    db: DatabaseSession,
    *,
    order: Order,
    customer: User,
) -> OperationsOrderRead:
    profile = db.get(
        CustomerProfile,
        customer.id,
    )

    items = db.scalars(
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
        .order_by(
            OrderItem.created_at,
            OrderItem.id,
        )
    ).all()
    shipments = db.scalars(
        select(OrderShipment)
        .where(OrderShipment.order_id == order.id)
        .order_by(OrderShipment.created_at.desc())
    ).all()
    shipment = shipments[0] if shipments else None
    charges = db.scalars(
        select(OrderCharge)
        .where(OrderCharge.order_id == order.id)
        .order_by(OrderCharge.sort_order, OrderCharge.created_at)
    ).all()
    cancellation = get_order_cancellation_request(
        db,
        order_id=order.id,
    )

    return OperationsOrderRead(
        id=str(order.id),
        status=order.status.value,
        fulfillment_status=order.fulfillment_status.value,
        cancellation_mode=cancellation_mode_for_order(order),
        cancellation=(
            operations_cancellation_read(cancellation)
            if cancellation is not None
            else None
        ),
        supplier_order_reference=order.supplier_order_reference,
        supplier_ordered_at=(
            order.supplier_ordered_at.isoformat()
            if order.supplier_ordered_at is not None
            else None
        ),
        received_ready_at=(
            order.received_ready_at.isoformat()
            if order.received_ready_at is not None
            else None
        ),
        shipped_at=(
            order.shipped_at.isoformat()
            if order.shipped_at is not None
            else None
        ),
        delivered_at=(
            order.delivered_at.isoformat()
            if order.delivered_at is not None
            else None
        ),
        subtotal_amount_minor=order.subtotal_amount_minor,
        charges_amount_minor=order.charges_amount_minor,
        total_amount_minor=order.total_amount_minor,
        currency=order.currency,
        delivery_address=order.delivery_address_snapshot,
        billing_address=order.billing_address_snapshot,
        charges=[
            {
                "kind": charge.kind,
                "label": charge.label,
                "amount_minor": charge.amount_minor,
            }
            for charge in charges
        ],
        created_at=order.created_at.isoformat(),
        customer=OperationsOrderCustomerRead(
            id=str(customer.id),
            email=customer.email,
            first_name=(
                profile.first_name
                if profile is not None
                else None
            ),
            last_name=(
                profile.last_name
                if profile is not None
                else None
            ),
            phone=(
                profile.phone
                if profile is not None
                else None
            ),
        ),
        items=[
            OperationsOrderItemRead(
                sku=item.sku_snapshot,
                name=item.name_snapshot,
                quantity=item.quantity,
                unit_amount_minor=item.unit_amount_minor,
                line_total_minor=item.line_total_minor,
                currency=item.currency,
                estimated_lead_time=item.estimated_lead_time_snapshot,
            )
            for item in items
        ],
        shipment=(
            OperationsOrderShipmentRead(
                carrier=shipment.carrier,
                tracking_number=shipment.tracking_number,
                tracking_url=shipment.tracking_url,
                shipped_at=(
                    order.shipped_at.isoformat()
                    if order.shipped_at is not None
                    else None
                ),
                delivered_at=(
                    order.delivered_at.isoformat()
                    if order.delivered_at is not None
                    else None
                ),
            )
            if shipment is not None
            else None
        ),
    )


@router.get(
    "/orders",
    response_model=list[OperationsOrderRead],
)
def list_orders(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsOrderRead]:
    require_operations(
        db,
        user=current_user,
    )

    orders = db.scalars(
        select(Order)
        .join(
            User,
            User.id == Order.user_id,
        )
        .join(
            UserRole,
            UserRole.user_id == User.id,
        )
        .where(
            UserRole.role == RoleName.customer
        )
        .order_by(
            Order.created_at.desc(),
            Order.id,
        )
        .limit(500)
    ).all()

    result: list[OperationsOrderRead] = []

    for order in orders:
        customer = db.get(
            User,
            order.user_id,
        )

        if customer is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail="Order customer record not found.",
            )

        result.append(
            operations_order_read(
                db,
                order=order,
                customer=customer,
            )
        )

    return result


@router.post(
    "/orders/{order_id}/fulfillment",
    response_model=OperationsOrderRead,
)
def update_order_fulfillment(
    order_id: uuid.UUID,
    payload: OrderFulfillmentUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsOrderRead:
    require_operations(
        db,
        user=current_user,
    )

    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    customer = db.get(User, order.user_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order customer record not found.",
        )

    try:
        transition_order_fulfillment(
            db,
            order=order,
            actor_user_id=current_user.id,
            new_status=payload.status,
            supplier_order_reference=payload.supplier_order_reference,
            carrier=payload.carrier,
            tracking_number=payload.tracking_number,
            tracking_url=payload.tracking_url,
        )
    except FulfillmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    db.commit()
    return operations_order_read(
        db,
        order=order,
        customer=customer,
    )


@router.post(
    "/orders/{order_id}/cancellation",
    response_model=OperationsOrderRead,
)
def review_order_cancellation_request(
    order_id: uuid.UUID,
    payload: OrderCancellationReviewUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsOrderRead:
    require_operations(
        db,
        user=current_user,
    )

    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    customer = db.get(User, order.user_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order customer record not found.",
        )

    cancellation = get_order_cancellation_request(
        db,
        order_id=order.id,
    )
    if cancellation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancellation request not found.",
        )

    try:
        review_order_cancellation(
            db,
            cancellation=cancellation,
            actor_user_id=current_user.id,
            action=payload.action,
            note=payload.note,
        )
    except CancellationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    db.commit()
    return operations_order_read(
        db,
        order=order,
        customer=customer,
    )


def operations_product_read(
    db: DatabaseSession,
    *,
    product: Product,
) -> OperationsProductRead:
    current_price = select_effective_price(product.prices)

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
            variant_id=(
                inventory.variant_id
                if inventory is not None
                else None
            ),
        )
        if inventory is not None
        else 0
    )

    return OperationsProductRead(
        id=str(product.id),
        sku=product.sku,
        name=product.name,
        category=product.category.name,
        manufacturer=product.manufacturer.name,
        product_family=product.product_family,
        system_type=product.system_type,
        active_variant_count=sum(
            1 for variant in product.variants if variant.active
        ),
        variants=[
            OperationsProductVariantRead(
                id=str(variant.id),
                sku=variant.sku,
                display_name=variant.display_name,
                option_values=variant.option_values,
            )
            for variant in product.variants
            if variant.active
        ],
        public_option_count=sum(
            1
            for relationship in product.related_options
            if relationship.active
            and relationship.public
            and not relationship.is_consumable
        ),
        relationships=[
            OperationsProductRelationshipRead(
                id=str(relationship.id),
                related_product_id=str(relationship.related_product_id),
                related_sku=relationship.related_product.sku,
                related_name=relationship.related_product.name,
                relationship_type=relationship.relationship_type,
                public=relationship.public,
                active=relationship.active,
                is_consumable=relationship.is_consumable,
                replacement_interval_days=relationship.replacement_interval_days,
                reminder_preference=relationship.reminder_preference,
                sort_order=relationship.sort_order,
            )
            for relationship in product.related_options
        ],
        active=product.active,
        assisted_sale_required=(
            product.assisted_sale_required
        ),
        online_sale_approved=(
            product.online_sale_approved
        ),
        warranty_documents=[
            {
                "id": str(document.id),
                "title": document.title,
                "version": document.version,
                "path": document.storage_path,
                "content_type": document.content_type,
                "checksum_sha256": document.checksum_sha256,
                "source_reference": document.source_reference,
                "public": document.public,
                "active": document.active,
                "verified_at": (
                    document.verified_at.isoformat()
                    if document.verified_at is not None
                    else None
                ),
            }
            for document in product.documents
            if document.document_type == ProductDocumentType.warranty
        ],
        pricing=OperationsPricingRead(
            mode=(
                current_price.pricing_policy_mode.value
                if current_price is not None
                else "NO_ONLINE_PRICE"
            ),
            amount_minor=(current_price.amount_minor if current_price is not None else None),
            currency=(current_price.currency if current_price is not None else None),
            effective_from=(
                current_price.effective_from.isoformat() if current_price is not None else None
            ),
        ),
        inventory=OperationsInventoryRead(
            status=(inventory.inventory_status.value if inventory is not None else "not_tracked"),
            quantity_on_hand=(inventory.quantity_on_hand if inventory is not None else 0),
            quantity_reserved=reserved_quantity,
            estimated_lead_time=(
                inventory.estimated_lead_time
                if inventory is not None
                else None
            ),
            source_kind=(
                inventory.source_kind
                if inventory is not None
                else "unspecified"
            ),
            source_reference=(
                inventory.source_reference
                if inventory is not None
                else None
            ),
            source_observed_at=(
                inventory.source_observed_at.isoformat()
                if inventory is not None
                and inventory.source_observed_at is not None
                else None
            ),
        ),
    )


def load_product_for_operations(
    db: DatabaseSession,
    product_id: uuid.UUID,
) -> Product | None:
    return db.scalar(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.manufacturer),
            selectinload(Product.prices),
            selectinload(Product.variants),
            selectinload(Product.documents),
            selectinload(Product.related_options).selectinload(
                ProductRelationship.related_product
            ),
        )
        .execution_options(
            populate_existing=True
        )
        .where(Product.id == product_id)
    )


@router.get("/catalog", response_model=list[OperationsProductRead])
def operations_catalog(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsProductRead]:
    require_operations(db, user=current_user)

    products = db.scalars(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.manufacturer),
            selectinload(Product.prices),
            selectinload(Product.variants),
            selectinload(Product.documents),
            selectinload(Product.related_options).selectinload(
                ProductRelationship.related_product
            ),
        )
        .order_by(Product.name)
    ).all()

    return [operations_product_read(db, product=product) for product in products]


def parse_relationship_product_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Related product ID must be a valid UUID.",
        ) from exc


@router.post(
    "/products/{product_id}/relationships",
    response_model=OperationsProductRead,
)
def create_product_relationship(
    product_id: uuid.UUID,
    payload: ProductRelationshipCreateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsProductRead:
    require_pricing_inventory_write(db, user=current_user)

    product = load_product_for_operations(db, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    related_product_id = parse_relationship_product_id(
        payload.related_product_id
    )
    if related_product_id == product.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A product cannot be related to itself.",
        )

    related_product = db.get(Product, related_product_id)
    if related_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related product not found.",
        )

    existing = db.scalar(
        select(ProductRelationship).where(
            ProductRelationship.product_id == product.id,
            ProductRelationship.related_product_id == related_product_id,
            ProductRelationship.relationship_type
            == payload.relationship_type,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That product relationship already exists.",
        )

    relationship = ProductRelationship(
        product_id=product.id,
        related_product_id=related_product_id,
        relationship_type=payload.relationship_type,
        public=payload.public,
        active=payload.active,
        is_consumable=payload.is_consumable,
        replacement_interval_days=payload.replacement_interval_days,
        reminder_preference=payload.reminder_preference,
        sort_order=payload.sort_order,
    )
    db.add(relationship)
    db.flush()

    record_audit_event(
        db,
        action="catalog.relationship_created",
        entity_type="product_relationship",
        entity_id=str(relationship.id),
        actor_user_id=current_user.id,
        metadata={
            "product_sku": product.sku,
            "related_sku": related_product.sku,
            "relationship_type": payload.relationship_type.value,
            "public": payload.public,
            "active": payload.active,
            "is_consumable": payload.is_consumable,
            "replacement_interval_days": payload.replacement_interval_days,
            "reminder_preference": (
                payload.reminder_preference.value
                if payload.reminder_preference is not None
                else None
            ),
            "sort_order": payload.sort_order,
        },
    )
    db.commit()

    refreshed = load_product_for_operations(db, product_id)
    if refreshed is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product refresh failed.",
        )
    return operations_product_read(db, product=refreshed)


@router.put(
    "/products/{product_id}/relationships/{relationship_id}",
    response_model=OperationsProductRead,
)
def update_product_relationship(
    product_id: uuid.UUID,
    relationship_id: uuid.UUID,
    payload: ProductRelationshipUpdateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsProductRead:
    require_pricing_inventory_write(db, user=current_user)

    relationship = db.scalar(
        select(ProductRelationship)
        .options(selectinload(ProductRelationship.related_product))
        .where(
            ProductRelationship.id == relationship_id,
            ProductRelationship.product_id == product_id,
        )
    )
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product relationship not found.",
        )

    duplicate = db.scalar(
        select(ProductRelationship).where(
            ProductRelationship.product_id == product_id,
            ProductRelationship.related_product_id
            == relationship.related_product_id,
            ProductRelationship.relationship_type
            == payload.relationship_type,
            ProductRelationship.id != relationship.id,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That product relationship already exists.",
        )

    relationship.relationship_type = payload.relationship_type
    relationship.public = payload.public
    relationship.active = payload.active
    relationship.is_consumable = payload.is_consumable
    relationship.replacement_interval_days = payload.replacement_interval_days
    relationship.reminder_preference = payload.reminder_preference
    relationship.sort_order = payload.sort_order
    db.flush()

    product = db.get(Product, product_id)
    record_audit_event(
        db,
        action="catalog.relationship_changed",
        entity_type="product_relationship",
        entity_id=str(relationship.id),
        actor_user_id=current_user.id,
        metadata={
            "product_sku": product.sku if product is not None else None,
            "related_sku": relationship.related_product.sku,
            "relationship_type": payload.relationship_type.value,
            "public": payload.public,
            "active": payload.active,
            "is_consumable": payload.is_consumable,
            "replacement_interval_days": payload.replacement_interval_days,
            "reminder_preference": (
                payload.reminder_preference.value
                if payload.reminder_preference is not None
                else None
            ),
            "sort_order": payload.sort_order,
        },
    )
    db.commit()

    refreshed = load_product_for_operations(db, product_id)
    if refreshed is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product refresh failed.",
        )
    return operations_product_read(db, product=refreshed)


@router.delete(
    "/products/{product_id}/relationships/{relationship_id}",
    response_model=OperationsProductRead,
)
def delete_product_relationship(
    product_id: uuid.UUID,
    relationship_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsProductRead:
    require_pricing_inventory_write(db, user=current_user)

    relationship = db.scalar(
        select(ProductRelationship)
        .options(selectinload(ProductRelationship.related_product))
        .where(
            ProductRelationship.id == relationship_id,
            ProductRelationship.product_id == product_id,
        )
    )
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product relationship not found.",
        )

    related_sku = relationship.related_product.sku
    relationship_type = relationship.relationship_type.value
    product = db.get(Product, product_id)
    db.delete(relationship)
    db.flush()

    record_audit_event(
        db,
        action="catalog.relationship_removed",
        entity_type="product_relationship",
        entity_id=str(relationship_id),
        actor_user_id=current_user.id,
        metadata={
            "product_sku": product.sku if product is not None else None,
            "related_sku": related_sku,
            "relationship_type": relationship_type,
        },
    )
    db.commit()

    refreshed = load_product_for_operations(db, product_id)
    if refreshed is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product refresh failed.",
        )
    return operations_product_read(db, product=refreshed)


@router.put(
    "/products/{product_id}/pricing",
    response_model=OperationsProductRead,
)
def update_product_pricing(
    product_id: uuid.UUID,
    payload: PricingUpdateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsProductRead:
    require_pricing_inventory_write(db, user=current_user)

    product = load_product_for_operations(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    now = datetime.now(UTC)

    prior_prices = db.scalars(
        select(ProductPrice).where(
            ProductPrice.product_id == product.id,
            ProductPrice.variant_id.is_(None),
            ProductPrice.active.is_(True),
        )
    ).all()

    for prior in prior_prices:
        prior.active = False
        prior.effective_until = now

    price = ProductPrice(
        product_id=product.id,
        variant_id=None,
        pricing_policy_mode=payload.mode,
        amount_minor=payload.amount_minor,
        currency=payload.currency,
        effective_from=now,
        active=True,
    )

    db.add(price)
    db.flush()

    record_audit_event(
        db,
        action="catalog.pricing_changed",
        entity_type="product",
        entity_id=str(product.id),
        actor_user_id=current_user.id,
        metadata={
            "sku": product.sku,
            "mode": payload.mode.value,
            "amount_minor": payload.amount_minor,
            "currency": payload.currency,
        },
    )

    db.commit()

    refreshed = load_product_for_operations(db, product_id)
    if refreshed is None:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Product refresh failed.",
        )

    return operations_product_read(db, product=refreshed)


@router.put(
    "/products/{product_id}/inventory",
    response_model=OperationsProductRead,
)
def update_product_inventory(
    product_id: uuid.UUID,
    payload: InventoryUpdateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsProductRead:
    require_pricing_inventory_write(db, user=current_user)

    product = load_product_for_operations(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    inventory = db.scalar(
        select(ProductInventory)
        .where(
            ProductInventory.product_id
            == product.id,
            ProductInventory.variant_id.is_(
                None
            ),
        )
        .with_for_update()
    )

    reserved_quantity = (
        active_reserved_quantity(
            db,
            product_id=product.id,
            variant_id=None,
        )
    )

    if (
        payload.quantity_on_hand
        < reserved_quantity
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "On-hand quantity cannot be "
                "below active cart reservations."
            ),
        )

    if inventory is None:
        inventory = ProductInventory(
            product_id=product.id,
            variant_id=None,
        )
        db.add(inventory)

    apply_inventory_observation(
        inventory,
        InventoryObservation(
            status=payload.status,
            quantity_on_hand=payload.quantity_on_hand,
            estimated_lead_time=payload.estimated_lead_time,
            source_kind=payload.source_kind,
            source_reference=payload.source_reference,
            observed_at=datetime.now(UTC),
        ),
    )

    db.flush()

    record_audit_event(
        db,
        action="catalog.inventory_changed",
        entity_type="product",
        entity_id=str(product.id),
        actor_user_id=current_user.id,
        metadata={
            "sku": product.sku,
            "status": payload.status.value,
            "quantity_on_hand": (
                payload.quantity_on_hand
            ),
            "quantity_reserved": (
                reserved_quantity
            ),
            "estimated_lead_time": (
                payload.estimated_lead_time
            ),
            "source_kind": payload.source_kind.value,
            "source_reference": payload.source_reference,
        },
    )

    db.commit()

    refreshed = load_product_for_operations(db, product_id)
    if refreshed is None:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Product refresh failed.",
        )

    return operations_product_read(db, product=refreshed)


@router.post(
    "/quotes/{quote_id}/formal-quotes",
    response_model=OperationsFormalQuoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_formal_quote(
    quote_id: uuid.UUID,
    payload: FormalQuoteCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsFormalQuoteRead:
    actor_roles = require_operations(db, user=current_user)
    quote = db.get(QuoteRequest, quote_id)
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote request not found.",
        )

    formal_quote = create_formal_quote_revision(
        db,
        quote_request=quote,
        lines=[
            FormalQuoteLineInput(
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_amount_minor=item.unit_amount_minor,
            )
            for item in payload.items
        ],
        charges=[
            FormalQuoteChargeInput(
                kind=charge.kind,
                label=charge.label,
                amount_minor=charge.amount_minor,
            )
            for charge in payload.charges
        ],
        delivery_address_snapshot=payload.delivery_address.model_dump(),
        billing_address_snapshot=payload.billing_address.model_dump(),
        customer_note=payload.customer_note,
        actor_user=current_user,
        actor_roles=actor_roles,
    )
    db.commit()
    db.refresh(formal_quote)
    return operations_formal_quote_read(formal_quote)


@router.post(
    "/formal-quotes/{formal_quote_id}/present",
    response_model=OperationsFormalQuoteRead,
)
def present_quote_to_customer(
    formal_quote_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsFormalQuoteRead:
    require_operations(db, user=current_user)
    formal_quote = db.scalar(
        select(FormalQuote)
        .options(
            selectinload(FormalQuote.items),
            selectinload(FormalQuote.charges),
            selectinload(FormalQuote.policy_snapshots),
            selectinload(FormalQuote.warranty_snapshots),
        )
        .where(FormalQuote.id == formal_quote_id)
    )
    if formal_quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formal quote not found.",
        )

    present_formal_quote(
        db,
        formal_quote=formal_quote,
        actor_user=current_user,
    )
    db.commit()
    db.refresh(formal_quote)
    return operations_formal_quote_read(formal_quote)

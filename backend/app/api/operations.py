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
    StockNotificationSubscription,
)
from app.models.commerce import (
    InstallerCandidate,
    Order,
    OrderCancellationRequest,
    OrderCharge,
    OrderItem,
    OrderShipment,
)
from app.models.communications import (
    CommunicationAttachment,
    CommunicationDirection,
    CommunicationEvent,
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
    UserStatus,
)
from app.models.launch import LaunchDependencyEvidence
from app.models.quote import (
    FormalQuote,
    QuoteRequest,
    QuoteRequestStatus,
)
from app.models.tax import (
    ProductTaxClassification,
    TaxCalculation,
)
from app.schemas.operations import (
    AvailabilityPolicyUpdateRequest,
    CustomerEquipmentCreateRequest,
    CustomerEquipmentUpdateRequest,
    FormalQuoteCreate,
    InstallerCandidateCreateRequest,
    InstallerCandidateUpdateRequest,
    InventoryUpdateRequest,
    LaunchDependencyEvidenceUpdateRequest,
    LaunchDependencyKey,
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
    OperationsInstallerCandidateRead,
    OperationsInventoryRead,
    OperationsLaunchDependencyEvidenceRead,
    OperationsLaunchReadinessCheckRead,
    OperationsLaunchReadinessRead,
    OperationsManufacturerClaimRead,
    OperationsOrderCancellationRead,
    OperationsOrderConfirmationRead,
    OperationsOrderCustomerRead,
    OperationsOrderItemRead,
    OperationsOrderRead,
    OperationsOrderShipmentRead,
    OperationsPricingRead,
    OperationsProductRead,
    OperationsProductRelationshipRead,
    OperationsProductSpecificationRead,
    OperationsProductVariantRead,
    OperationsPromotionRead,
    OperationsQuoteRead,
    OperationsReturnPolicyExceptionRead,
    OperationsSalesInsightsRead,
    OperationsStockNotificationRead,
    OperationsSummaryRead,
    OperationsTaxCalculationRead,
    OperationsTaxClassificationRead,
    OrderCancellationExceptionCreate,
    OrderCancellationReviewUpdate,
    OrderFulfillmentUpdate,
    OrderReturnPolicyExceptionCreate,
    PricingUpdateRequest,
    ProductRelationshipCreateRequest,
    ProductRelationshipUpdateRequest,
    PromotionCreateRequest,
    QuoteNotesUpdate,
    QuoteStatusUpdate,
    TaxClassificationUpdateRequest,
)
from app.services.audit import record_audit_event
from app.services.cancellations import (
    CLOSED_AFTER_SUPPLIER_CONFIRMATION,
    CancellationError,
    cancellation_mode_for_order,
    get_order_cancellation_request,
    request_order_cancellation,
    review_order_cancellation,
)
from app.services.catalog_publication import product_is_publicly_visible
from app.services.commerce import (
    active_reserved_quantity,
)
from app.services.commercial_costs import commercial_cost_breakdown
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
    complete_formal_quote_staff_review,
    create_formal_quote_revision,
    present_formal_quote,
    shipping_insurance_amount_minor,
)
from app.services.fulfillment import (
    FulfillmentError,
    transition_order_fulfillment,
)
from app.services.inventory_observations import (
    InventoryObservation,
    apply_inventory_observation,
)
from app.services.launch_readiness import build_launch_readiness
from app.services.operations_access import (
    require_audit_log_read,
    require_cancellation_exception_write,
    require_customer_equipment_write,
    require_installer_candidate_write,
    require_launch_dependency_write,
    require_operations,
    require_pricing_inventory_write,
    require_return_policy_exception_write,
)
from app.services.order_confirmations import (
    OrderConfirmationError,
    latest_order_confirmation_delivery,
    send_order_confirmation,
)
from app.services.order_lifecycle import customer_order_stage
from app.services.pricing import (
    promotion_mode_supported,
    promotion_windows_overlap,
    select_effective_price,
    select_standard_price,
)
from app.services.return_policy_exceptions import (
    ReturnPolicyExceptionError,
    ReturnPolicyExceptionEvidence,
    authorize_return_policy_exception,
    list_return_policy_exceptions,
    refund_policy_snapshot_for_order,
)
from app.services.sales_insights import summarize_assisted_sales
from app.services.stock_notifications import (
    dispatch_back_in_stock_notifications,
    inventory_is_staff_confirmed_available,
)
from app.services.tax_automation import (
    TaxAutomationError,
    calculate_formal_quote_tax,
    calculate_order_tax,
)

router = APIRouter(prefix="/operations", tags=["operations"])


LAUNCH_DEPENDENCIES: tuple[tuple[LaunchDependencyKey, str], ...] = (
    ("tax", "Automated tax"),
    ("payment_checkout", "Payment / Affinity24"),
    ("legal_review", "Legal review"),
    ("shipping_insurance", "Shipping insurance"),
    ("support_phone", "Public support phone"),
    ("installer_program", "Installer program"),
)

LAUNCH_DEPENDENCY_LABELS = dict(LAUNCH_DEPENDENCIES)


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
        cost_breakdown=commercial_cost_breakdown(
            subtotal_amount_minor=formal_quote.subtotal_amount_minor,
            charges=formal_quote.charges,
            expected_total_amount_minor=formal_quote.total_amount_minor,
        ).as_dict(),
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
        shipping_insurance_offered=(
            shipping_insurance_amount_minor(formal_quote) > 0
        ),
        shipping_insurance_decision=formal_quote.shipping_insurance_decision,
        shipping_insurance_decided_at=(
            formal_quote.shipping_insurance_decided_at.isoformat()
            if formal_quote.shipping_insurance_decided_at is not None
            else None
        ),
        shipping_insurance_decided_by_user_id=(
            str(formal_quote.shipping_insurance_decided_by_user_id)
            if formal_quote.shipping_insurance_decided_by_user_id is not None
            else None
        ),
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
        staff_review_required=formal_quote.staff_review_required,
        staff_review_reasons=list(formal_quote.staff_review_reasons),
        staff_review_completed_at=(
            formal_quote.staff_review_completed_at.isoformat()
            if formal_quote.staff_review_completed_at is not None
            else None
        ),
        staff_review_completed_by_user_id=(
            str(formal_quote.staff_review_completed_by_user_id)
            if formal_quote.staff_review_completed_by_user_id is not None
            else None
        ),
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


def operations_tax_calculation_read(
    calculation: TaxCalculation,
) -> OperationsTaxCalculationRead:
    return OperationsTaxCalculationRead(
        id=str(calculation.id),
        provider=calculation.provider,
        provider_calculation_id=calculation.provider_calculation_id,
        context_type=(
            "formal_quote"
            if calculation.formal_quote_id is not None
            else "order"
        ),
        currency=calculation.currency,
        line_items_amount_minor=calculation.line_items_amount_minor,
        shipping_amount_minor=calculation.shipping_amount_minor,
        tax_amount_minor=calculation.tax_amount_minor,
        amount_total_minor=calculation.amount_total_minor,
        livemode=calculation.livemode,
        expires_at=(
            calculation.expires_at.isoformat()
            if calculation.expires_at is not None
            else None
        ),
        created_at=calculation.created_at.isoformat(),
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

    failed_deliveries = db.scalars(
        select(EmailDelivery).where(
            EmailDelivery.status == EmailDeliveryStatus.failed
        )
    ).all()
    failed_email_deliveries = sum(
        1
        for delivery in failed_deliveries
        if email_delivery_requires_review(
            db,
            delivery=delivery,
        )
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
    "/launch-readiness",
    response_model=OperationsLaunchReadinessRead,
)
def operations_launch_readiness(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsLaunchReadinessRead:
    require_operations(db, user=current_user)
    snapshot = build_launch_readiness(db)

    return OperationsLaunchReadinessRead(
        status=snapshot.status,
        ready_count=snapshot.ready_count,
        action_required_count=snapshot.action_required_count,
        deferred_count=snapshot.deferred_count,
        launch_phase=snapshot.launch_phase,
        launch_phase_label=snapshot.launch_phase_label,
        commerce_checkout_allowed=snapshot.commerce_checkout_allowed,
        commerce_gate_detail=snapshot.commerce_gate_detail,
        commerce_blockers=list(snapshot.commerce_blockers),
        evaluated_at=datetime.now(UTC).isoformat(),
        checks=[
            OperationsLaunchReadinessCheckRead(
                key=check.key,
                label=check.label,
                status=check.status,
                detail=check.detail,
                evidence=list(check.evidence),
            )
            for check in snapshot.checks
        ],
    )


def operations_launch_dependency_evidence_read(
    dependency_key: LaunchDependencyKey,
    evidence: LaunchDependencyEvidence | None,
) -> OperationsLaunchDependencyEvidenceRead:
    return OperationsLaunchDependencyEvidenceRead(
        dependency_key=dependency_key,
        label=LAUNCH_DEPENDENCY_LABELS[dependency_key],
        tracking_status=(
            evidence.tracking_status
            if evidence is not None
            else "action_required"
        ),
        source_reference=(
            evidence.source_reference
            if evidence is not None
            else None
        ),
        evidence_received_at=(
            evidence.evidence_received_at.isoformat()
            if evidence is not None and evidence.evidence_received_at is not None
            else None
        ),
        internal_notes=(
            evidence.internal_notes
            if evidence is not None
            else None
        ),
        created_by_user_id=(
            str(evidence.created_by_user_id)
            if evidence is not None
            else None
        ),
        updated_by_user_id=(
            str(evidence.updated_by_user_id)
            if evidence is not None
            else None
        ),
        created_at=(
            evidence.created_at.isoformat()
            if evidence is not None
            else None
        ),
        updated_at=(
            evidence.updated_at.isoformat()
            if evidence is not None
            else None
        ),
    )


@router.get(
    "/launch-dependency-evidence",
    response_model=list[OperationsLaunchDependencyEvidenceRead],
)
def list_launch_dependency_evidence(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsLaunchDependencyEvidenceRead]:
    require_operations(db, user=current_user)

    rows = {
        row.dependency_key: row
        for row in db.scalars(
            select(LaunchDependencyEvidence)
        ).all()
    }

    return [
        operations_launch_dependency_evidence_read(
            dependency_key,
            rows.get(dependency_key),
        )
        for dependency_key, _label in LAUNCH_DEPENDENCIES
    ]


@router.patch(
    "/launch-dependency-evidence/{dependency_key}",
    response_model=OperationsLaunchDependencyEvidenceRead,
)
def update_launch_dependency_evidence(
    dependency_key: LaunchDependencyKey,
    payload: LaunchDependencyEvidenceUpdateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsLaunchDependencyEvidenceRead:
    require_launch_dependency_write(db, user=current_user)

    evidence = db.get(
        LaunchDependencyEvidence,
        dependency_key,
    )
    previous_status = (
        evidence.tracking_status
        if evidence is not None
        else None
    )

    if evidence is None:
        evidence = LaunchDependencyEvidence(
            dependency_key=dependency_key,
            tracking_status=payload.tracking_status,
            source_reference=payload.source_reference,
            evidence_received_at=payload.evidence_received_at,
            internal_notes=payload.internal_notes,
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id,
        )
        db.add(evidence)
    else:
        evidence.tracking_status = payload.tracking_status
        evidence.source_reference = payload.source_reference
        evidence.evidence_received_at = payload.evidence_received_at
        evidence.internal_notes = payload.internal_notes
        evidence.updated_by_user_id = current_user.id

    db.flush()

    record_audit_event(
        db,
        action="launch_dependency_evidence.updated",
        entity_type="launch_dependency_evidence",
        entity_id=dependency_key,
        actor_user_id=current_user.id,
        metadata={
            "dependency_key": dependency_key,
            "previous_status": previous_status,
            "new_status": evidence.tracking_status,
            "has_source_reference": bool(evidence.source_reference),
            "has_internal_notes": bool(evidence.internal_notes),
            "evidence_received_at_recorded": evidence.evidence_received_at is not None,
            "commerce_gate_effect": "none",
        },
    )

    db.commit()
    db.refresh(evidence)

    return operations_launch_dependency_evidence_read(
        dependency_key,
        evidence,
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


def email_delivery_requires_review(
    db: DatabaseSession,
    *,
    delivery: EmailDelivery,
) -> bool:
    if delivery.status != EmailDeliveryStatus.failed:
        return False

    if delivery.category != "email_verification":
        return True

    if (
        delivery.related_entity_type != "user"
        or not delivery.related_entity_id
    ):
        return True

    try:
        user_id = uuid.UUID(delivery.related_entity_id)
    except ValueError:
        return True

    user = db.get(User, user_id)
    if user is None:
        return False

    if user.email_verified_at is not None:
        return False

    return user.status != UserStatus.disabled


def operations_communication_read(
    db: DatabaseSession,
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
        requires_review=email_delivery_requires_review(
            db,
            delivery=delivery,
        ),
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
            db,
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
    if thread.related_entity_type == "quote_request":
        if thread.related_entity_id is None:
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

    if thread.related_entity_type != "support_request":
        return None

    message = db.scalar(
        select(CommunicationMessage)
        .where(
            CommunicationMessage.thread_id == thread.id,
            CommunicationMessage.direction == CommunicationDirection.inbound,
        )
        .order_by(
            CommunicationMessage.created_at,
            CommunicationMessage.id,
        )
    )
    if message is None:
        return None

    event = db.scalar(
        select(CommunicationEvent)
        .where(
            CommunicationEvent.message_id == message.id,
            CommunicationEvent.event_type == "support_request_submitted",
        )
        .order_by(CommunicationEvent.occurred_at)
    )
    details = event.details if event is not None and event.details is not None else {}

    kind_value = details.get("kind")
    kind = kind_value if isinstance(kind_value, str) else "general_support"
    request_type = {
        "warranty": "website_warranty_support_request",
        "product_support": "website_product_support_request",
        "general_support": "website_general_support_request",
    }.get(kind, "website_general_support_request")

    name_value = details.get("name")
    email_value = details.get("email")
    phone_value = details.get("phone")
    product_name_value = details.get("product_name")

    created_at = message.received_at or message.created_at
    return OperationsCommunicationOriginatingRequestRead(
        request_type=request_type,
        name=(
            name_value
            if isinstance(name_value, str) and name_value.strip()
            else message.sender_name or "Customer"
        ),
        email=(
            email_value
            if isinstance(email_value, str) and email_value.strip()
            else message.sender_address
        ),
        phone=(phone_value if isinstance(phone_value, str) else None),
        product_name=(
            product_name_value
            if isinstance(product_name_value, str) and product_name_value.strip()
            else None
        ),
        message=message.body_text,
        created_at=created_at.isoformat(),
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
            selectinload(QuoteRequest.formal_quotes).selectinload(
                FormalQuote.warranty_snapshots
            ),
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


def operations_installer_candidate_read(
    candidate: InstallerCandidate,
) -> OperationsInstallerCandidateRead:
    return OperationsInstallerCandidateRead(
        id=str(candidate.id),
        business_name=candidate.business_name,
        contact_name=candidate.contact_name,
        email=candidate.email,
        phone=candidate.phone,
        website=candidate.website,
        service_area_notes=candidate.service_area_notes,
        source_reference=candidate.source_reference,
        status=candidate.status,
        internal_notes=candidate.internal_notes,
        created_by_user_id=str(candidate.created_by_user_id),
        updated_by_user_id=str(candidate.updated_by_user_id),
        created_at=candidate.created_at.isoformat(),
        updated_at=candidate.updated_at.isoformat(),
    )


@router.get(
    "/installer-candidates",
    response_model=list[OperationsInstallerCandidateRead],
)
def list_installer_candidates(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsInstallerCandidateRead]:
    require_operations(db, user=current_user)

    candidates = db.scalars(
        select(InstallerCandidate).order_by(
            InstallerCandidate.updated_at.desc(),
            InstallerCandidate.business_name,
        )
    ).all()

    return [
        operations_installer_candidate_read(candidate)
        for candidate in candidates
    ]


@router.post(
    "/installer-candidates",
    response_model=OperationsInstallerCandidateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_installer_candidate(
    payload: InstallerCandidateCreateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsInstallerCandidateRead:
    require_installer_candidate_write(db, user=current_user)

    candidate = InstallerCandidate(
        **payload.model_dump(),
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
    )
    db.add(candidate)
    db.flush()

    record_audit_event(
        db,
        action="installer_candidate.created",
        entity_type="installer_candidate",
        entity_id=str(candidate.id),
        actor_user_id=current_user.id,
        metadata={
            "business_name": candidate.business_name,
            "status": candidate.status,
        },
    )

    db.commit()
    db.refresh(candidate)
    return operations_installer_candidate_read(candidate)


@router.patch(
    "/installer-candidates/{candidate_id}",
    response_model=OperationsInstallerCandidateRead,
)
def update_installer_candidate(
    candidate_id: uuid.UUID,
    payload: InstallerCandidateUpdateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsInstallerCandidateRead:
    require_installer_candidate_write(db, user=current_user)

    candidate = db.get(InstallerCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installer candidate not found.",
        )

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No installer candidate changes were supplied.",
        )
    if "business_name" in changes and changes["business_name"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Business name cannot be cleared.",
        )
    if "status" in changes and changes["status"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Installer candidate status cannot be cleared.",
        )

    changed_fields = sorted(changes)
    previous_status = candidate.status
    for field, value in changes.items():
        setattr(candidate, field, value)
    candidate.updated_by_user_id = current_user.id

    record_audit_event(
        db,
        action="installer_candidate.updated",
        entity_type="installer_candidate",
        entity_id=str(candidate.id),
        actor_user_id=current_user.id,
        metadata={
            "changed_fields": changed_fields,
            "previous_status": previous_status,
            "new_status": candidate.status,
        },
    )

    db.commit()
    db.refresh(candidate)
    return operations_installer_candidate_read(candidate)


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


def operations_return_policy_exception_read(
    exception: ReturnPolicyExceptionEvidence,
) -> OperationsReturnPolicyExceptionRead:
    return OperationsReturnPolicyExceptionRead(
        id=exception.id,
        actor_user_id=exception.actor_user_id,
        created_at=exception.created_at.isoformat(),
        policy_snapshot_id=exception.policy_snapshot_id,
        policy_version=exception.policy_version,
        reason=exception.reason,
        return_window_days_override=(
            exception.return_window_days_override
        ),
        restocking_fee_basis_points_override=(
            exception.restocking_fee_basis_points_override
        ),
        customer_pays_return_shipping_override=(
            exception.customer_pays_return_shipping_override
        ),
        refund_outbound_shipping_override=(
            exception.refund_outbound_shipping_override
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
    refund_policy_snapshot = refund_policy_snapshot_for_order(
        db,
        order=order,
    )
    return_policy_exceptions = list_return_policy_exceptions(
        db,
        order_id=order.id,
    )
    order_confirmation_delivery = latest_order_confirmation_delivery(
        db,
        order_id=order.id,
    )

    return OperationsOrderRead(
        id=str(order.id),
        status=order.status.value,
        fulfillment_status=order.fulfillment_status.value,
        customer_status=customer_order_stage(order).value,
        cancellation_mode=cancellation_mode_for_order(order),
        cancellation=(
            operations_cancellation_read(cancellation)
            if cancellation is not None
            else None
        ),
        order_confirmation=(
            OperationsOrderConfirmationRead(
                delivery_id=str(order_confirmation_delivery.id),
                status=order_confirmation_delivery.status.value,
                attempted_at=order_confirmation_delivery.created_at.isoformat(),
                sent_at=(
                    order_confirmation_delivery.sent_at.isoformat()
                    if order_confirmation_delivery.sent_at is not None
                    else None
                ),
                error_summary=order_confirmation_delivery.error_summary,
            )
            if order_confirmation_delivery is not None
            else OperationsOrderConfirmationRead()
        ),
        refund_policy_snapshot=(
            {
                "id": refund_policy_snapshot.id,
                "kind": refund_policy_snapshot.kind,
                "version": refund_policy_snapshot.version_snapshot,
                "title": refund_policy_snapshot.title_snapshot,
                "body": refund_policy_snapshot.body_snapshot,
                "refund_terms": refund_policy_snapshot.structured_terms_snapshot,
                "content_sha256": refund_policy_snapshot.content_sha256,
                "structured_terms_sha256": (
                    refund_policy_snapshot.structured_terms_sha256
                ),
                "effective_at": refund_policy_snapshot.effective_at_snapshot,
            }
            if refund_policy_snapshot is not None
            else None
        ),
        return_policy_exceptions=[
            operations_return_policy_exception_read(exception)
            for exception in return_policy_exceptions
        ],
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
    "/orders/{order_id}/tax-calculation",
    response_model=OperationsTaxCalculationRead,
)
def calculate_awaiting_payment_order_tax(
    order_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsTaxCalculationRead:
    require_pricing_inventory_write(db, user=current_user)

    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    try:
        calculation = calculate_order_tax(
            db,
            order=order,
            actor_user_id=current_user.id,
        )
    except TaxAutomationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    db.commit()
    db.refresh(calculation)
    return operations_tax_calculation_read(calculation)


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
    "/orders/{order_id}/confirmation",
    response_model=OperationsOrderRead,
)
def send_customer_order_confirmation(
    order_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsOrderRead:
    require_operations(
        db,
        user=current_user,
    )

    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
    )
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
        send_order_confirmation(
            db,
            order=order,
            customer=customer,
            settings=get_email_runtime_settings(),
            actor_user_id=current_user.id,
        )
    except OrderConfirmationError as exc:
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
    "/orders/{order_id}/cancellation-exception",
    response_model=OperationsOrderRead,
)
def start_order_cancellation_exception_review(
    order_id: uuid.UUID,
    payload: OrderCancellationExceptionCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsOrderRead:
    require_cancellation_exception_write(
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

    if cancellation_mode_for_order(order) != CLOSED_AFTER_SUPPLIER_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Exceptional cancellation review is only available after "
                "Supplier Confirmed."
            ),
        )

    try:
        request_order_cancellation(
            db,
            order=order,
            actor_user_id=current_user.id,
            reason=payload.reason,
            allow_post_confirmation_exception=True,
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
    require_cancellation_exception_write(
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


@router.post(
    "/orders/{order_id}/return-policy-exceptions",
    response_model=OperationsOrderRead,
)
def authorize_order_return_policy_exception(
    order_id: uuid.UUID,
    payload: OrderReturnPolicyExceptionCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsOrderRead:
    require_return_policy_exception_write(
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
        authorize_return_policy_exception(
            db,
            order=order,
            actor_user_id=current_user.id,
            reason=payload.reason,
            return_window_days_override=(
                payload.return_window_days_override
            ),
            restocking_fee_basis_points_override=(
                payload.restocking_fee_basis_points_override
            ),
            customer_pays_return_shipping_override=(
                payload.customer_pays_return_shipping_override
            ),
            refund_outbound_shipping_override=(
                payload.refund_outbound_shipping_override
            ),
        )
    except ReturnPolicyExceptionError as exc:
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
    now = datetime.now(UTC)
    current_price = select_effective_price(product.prices, now=now)
    standard_price = select_standard_price(product.prices, now=now)
    promotions = sorted(
        (
            price
            for price in product.prices
            if price.active
            and price.variant_id is None
            and price.effective_until is not None
            and price.effective_until > now
        ),
        key=lambda price: price.effective_from,
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
            variant_id=(
                inventory.variant_id
                if inventory is not None
                else None
            ),
        )
        if inventory is not None
        else 0
    )

    tax_classification = db.scalar(
        select(ProductTaxClassification).where(
            ProductTaxClassification.product_id == product.id,
            ProductTaxClassification.provider == "stripe_tax",
            ProductTaxClassification.active.is_(True),
        )
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
            and relationship.relationship_type.value != "replacement"
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
        lifecycle_status=product.lifecycle_status,
        public_retire_at=product.public_retire_at,
        public_catalog_visible=product_is_publicly_visible(product),
        allow_inquiry_when_unavailable=product.allow_inquiry_when_unavailable,
        allow_formal_quote_when_unavailable=product.allow_formal_quote_when_unavailable,
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
        specifications=[
            OperationsProductSpecificationRead(
                id=str(specification.id),
                spec_key=specification.spec_key,
                label=specification.label,
                value_text=specification.value_text,
                unit=specification.unit,
                source_reference=specification.source_reference,
                public=specification.public,
                active=specification.active,
                verified_at=(
                    specification.verified_at.isoformat()
                    if specification.verified_at is not None
                    else None
                ),
            )
            for specification in product.specifications
        ],
        manufacturer_claims=[
            OperationsManufacturerClaimRead(
                id=str(claim.id),
                claim_text=claim.claim_text,
                source_reference=claim.source_reference,
                approved_by=claim.approved_by,
                approved_at=(
                    claim.approved_at.isoformat()
                    if claim.approved_at is not None
                    else None
                ),
                expires_at=(
                    claim.expires_at.isoformat()
                    if claim.expires_at is not None
                    else None
                ),
                active=claim.active,
                public_ready=(
                    claim.active
                    and claim.approved_at is not None
                    and claim.approved_at <= now
                    and bool(claim.claim_text.strip())
                    and bool(claim.source_reference.strip())
                    and (claim.expires_at is None or claim.expires_at > now)
                ),
            )
            for claim in product.approved_claims
        ],
        tax_classification=(
            OperationsTaxClassificationRead(
                provider=tax_classification.provider,
                tax_code=tax_classification.tax_code,
                source_reference=tax_classification.source_reference,
                verified_at=tax_classification.verified_at.isoformat(),
                verified_by_user_id=(
                    str(tax_classification.verified_by_user_id)
                    if tax_classification.verified_by_user_id is not None
                    else None
                ),
                active=tax_classification.active,
            )
            if tax_classification is not None
            else None
        ),
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
            effective_until=(
                current_price.effective_until.isoformat()
                if current_price is not None and current_price.effective_until is not None
                else None
            ),
        ),
        standard_pricing=OperationsPricingRead(
            mode=(
                standard_price.pricing_policy_mode.value
                if standard_price is not None
                else "NO_ONLINE_PRICE"
            ),
            amount_minor=(standard_price.amount_minor if standard_price is not None else None),
            currency=(standard_price.currency if standard_price is not None else None),
            effective_from=(
                standard_price.effective_from.isoformat() if standard_price is not None else None
            ),
            effective_until=None,
        ),
        promotions=[
            OperationsPromotionRead(
                id=str(price.id),
                mode=price.pricing_policy_mode.value,
                amount_minor=price.amount_minor or 0,
                currency=price.currency,
                effective_from=price.effective_from.isoformat(),
                effective_until=price.effective_until.isoformat(),
                state=("scheduled" if price.effective_from > now else "active"),
            )
            for price in promotions
            if price.amount_minor is not None
        ],
        inventory=OperationsInventoryRead(
            status=(inventory.inventory_status.value if inventory is not None else "not_tracked"),
            quantity_on_hand=(inventory.quantity_on_hand if inventory is not None else 0),
            quantity_reserved=reserved_quantity,
            expected_available_on=(
                inventory.expected_available_on
                if inventory is not None
                else None
            ),
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
            selectinload(Product.specifications),
            selectinload(Product.approved_claims),
            selectinload(Product.related_options).selectinload(
                ProductRelationship.related_product
            ),
        )
        .execution_options(
            populate_existing=True
        )
        .where(Product.id == product_id)
    )


@router.get(
    "/stock-notifications",
    response_model=list[OperationsStockNotificationRead],
)
def list_stock_notifications(
    db: DatabaseSession,
    current_user: CurrentUser,
    active_only: bool = Query(default=True),
) -> list[OperationsStockNotificationRead]:
    require_operations(db, user=current_user)

    statement = (
        select(StockNotificationSubscription, Product)
        .join(
            Product,
            Product.id == StockNotificationSubscription.product_id,
        )
        .order_by(
            StockNotificationSubscription.created_at.desc(),
            Product.name,
            StockNotificationSubscription.email,
        )
    )

    if active_only:
        statement = statement.where(
            StockNotificationSubscription.active.is_(True)
        )

    rows = db.execute(statement).all()

    return [
        OperationsStockNotificationRead(
            id=str(subscription.id),
            product_id=str(product.id),
            product_sku=product.sku,
            product_name=product.name,
            email=subscription.email,
            active=subscription.active,
            notified_at=(
                subscription.notified_at.isoformat()
                if subscription.notified_at is not None
                else None
            ),
            created_at=subscription.created_at.isoformat(),
            updated_at=subscription.updated_at.isoformat(),
        )
        for subscription, product in rows
    ]


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
    "/products/{product_id}/tax-classification",
    response_model=OperationsProductRead,
)
def update_product_tax_classification(
    product_id: uuid.UUID,
    payload: TaxClassificationUpdateRequest,
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
    classification = db.scalar(
        select(ProductTaxClassification).where(
            ProductTaxClassification.product_id == product.id,
            ProductTaxClassification.provider == "stripe_tax",
        )
    )
    if classification is None:
        classification = ProductTaxClassification(
            product_id=product.id,
            provider="stripe_tax",
            tax_code=payload.tax_code,
            source_reference=payload.source_reference,
            verified_by_user_id=current_user.id,
            verified_at=now,
            active=True,
        )
        db.add(classification)
    else:
        classification.tax_code = payload.tax_code
        classification.source_reference = payload.source_reference
        classification.verified_by_user_id = current_user.id
        classification.verified_at = now
        classification.active = True

    db.flush()
    record_audit_event(
        db,
        action="catalog.tax_classification_changed",
        entity_type="product",
        entity_id=str(product.id),
        actor_user_id=current_user.id,
        metadata={
            "sku": product.sku,
            "provider": "stripe_tax",
            "tax_code": payload.tax_code,
            "source_reference": payload.source_reference,
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

    active_or_scheduled_promotions = [
        price
        for price in product.prices
        if price.active
        and price.variant_id is None
        and price.effective_until is not None
        and price.effective_until > now
    ]
    if active_or_scheduled_promotions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cancel active or scheduled promotions before changing "
                "the standard pricing policy."
            ),
        )

    prior_prices = db.scalars(
        select(ProductPrice).where(
            ProductPrice.product_id == product.id,
            ProductPrice.variant_id.is_(None),
            ProductPrice.active.is_(True),
            ProductPrice.effective_until.is_(None),
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


@router.post(
    "/products/{product_id}/promotions",
    response_model=OperationsProductRead,
)
def schedule_product_promotion(
    product_id: uuid.UUID,
    payload: PromotionCreateRequest,
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
    if payload.effective_until <= now:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Promotion end must be in the future.",
        )

    standard_price = select_standard_price(product.prices, now=now)
    if standard_price is None or standard_price.amount_minor is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Set an authoritative standard price before scheduling a promotion."
            ),
        )

    if not promotion_mode_supported(standard_price.pricing_policy_mode):
        detail = (
            "MAP-limited promotions require verified manufacturer promotional "
            "terms and are not scheduled through this launch workflow."
            if standard_price.pricing_policy_mode.value == "MAP_LIMITED"
            else "This pricing policy does not support scheduled promotions."
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    if payload.amount_minor >= standard_price.amount_minor:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Promotional price must be lower than the standard price.",
        )

    for existing in product.prices:
        if (
            existing.active
            and existing.variant_id is None
            and existing.effective_until is not None
            and existing.effective_until > now
            and promotion_windows_overlap(
                existing_from=existing.effective_from,
                existing_until=existing.effective_until,
                proposed_from=payload.effective_from,
                proposed_until=payload.effective_until,
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Promotion window overlaps another scheduled promotion.",
            )

    promotion = ProductPrice(
        product_id=product.id,
        variant_id=None,
        pricing_policy_mode=standard_price.pricing_policy_mode,
        amount_minor=payload.amount_minor,
        currency=standard_price.currency,
        effective_from=payload.effective_from,
        effective_until=payload.effective_until,
        active=True,
    )
    db.add(promotion)
    db.flush()

    record_audit_event(
        db,
        action="catalog.promotion_scheduled",
        entity_type="product_price",
        entity_id=str(promotion.id),
        actor_user_id=current_user.id,
        metadata={
            "product_id": str(product.id),
            "sku": product.sku,
            "mode": promotion.pricing_policy_mode.value,
            "amount_minor": promotion.amount_minor,
            "currency": promotion.currency,
            "effective_from": promotion.effective_from.isoformat(),
            "effective_until": promotion.effective_until.isoformat(),
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
    "/products/{product_id}/promotions/{promotion_id}",
    response_model=OperationsProductRead,
)
def cancel_product_promotion(
    product_id: uuid.UUID,
    promotion_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsProductRead:
    require_pricing_inventory_write(db, user=current_user)

    promotion = db.scalar(
        select(ProductPrice).where(
            ProductPrice.id == promotion_id,
            ProductPrice.product_id == product_id,
            ProductPrice.variant_id.is_(None),
            ProductPrice.effective_until.is_not(None),
            ProductPrice.active.is_(True),
        )
    )
    if promotion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active promotion not found.",
        )

    product = db.get(Product, product_id)
    promotion.active = False
    record_audit_event(
        db,
        action="catalog.promotion_cancelled",
        entity_type="product_price",
        entity_id=str(promotion.id),
        actor_user_id=current_user.id,
        metadata={
            "product_id": str(product_id),
            "sku": product.sku if product is not None else None,
            "effective_from": promotion.effective_from.isoformat(),
            "effective_until": (
                promotion.effective_until.isoformat()
                if promotion.effective_until is not None
                else None
            ),
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
    "/products/{product_id}/availability-policy",
    response_model=OperationsProductRead,
)
def update_product_availability_policy(
    product_id: uuid.UUID,
    payload: AvailabilityPolicyUpdateRequest,
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

    product.lifecycle_status = payload.lifecycle_status
    product.public_retire_at = payload.public_retire_at
    product.allow_inquiry_when_unavailable = payload.allow_inquiry_when_unavailable
    product.allow_formal_quote_when_unavailable = (
        payload.allow_formal_quote_when_unavailable
    )

    record_audit_event(
        db,
        action="catalog.availability_policy_changed",
        entity_type="product",
        entity_id=str(product.id),
        actor_user_id=current_user.id,
        metadata={
            "sku": product.sku,
            "lifecycle_status": payload.lifecycle_status.value,
            "public_retire_at": (
                payload.public_retire_at.isoformat()
                if payload.public_retire_at is not None
                else None
            ),
            "allow_inquiry_when_unavailable": payload.allow_inquiry_when_unavailable,
            "allow_formal_quote_when_unavailable": (
                payload.allow_formal_quote_when_unavailable
            ),
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
            expected_available_on=payload.expected_available_on,
            estimated_lead_time=payload.estimated_lead_time,
            source_kind=payload.source_kind,
            source_reference=payload.source_reference,
            observed_at=datetime.now(UTC),
        ),
    )

    db.flush()

    notification_summary = None

    if inventory_is_staff_confirmed_available(
        status=payload.status,
        quantity_on_hand=payload.quantity_on_hand,
        quantity_reserved=reserved_quantity,
        lifecycle_status=product.lifecycle_status,
    ):
        notification_summary = dispatch_back_in_stock_notifications(
            db,
            product=product,
            settings=get_email_runtime_settings(),
            actor_user_id=current_user.id,
        )

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
            "expected_available_on": (
                payload.expected_available_on.isoformat()
                if payload.expected_available_on is not None
                else None
            ),
            "estimated_lead_time": (
                payload.estimated_lead_time
            ),
            "source_kind": payload.source_kind.value,
            "source_reference": payload.source_reference,
            "stock_notifications": (
                {
                    "attempted": notification_summary.attempted,
                    "sent": notification_summary.sent,
                    "failed": notification_summary.failed,
                    "suppressed": notification_summary.suppressed,
                }
                if notification_summary is not None
                else None
            ),
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
        manual_staff_review_required=payload.manual_staff_review_required,
        actor_user=current_user,
        actor_roles=actor_roles,
    )
    db.commit()
    db.refresh(formal_quote)
    return operations_formal_quote_read(formal_quote)


@router.post(
    "/formal-quotes/{formal_quote_id}/tax-calculation",
    response_model=OperationsTaxCalculationRead,
)
def calculate_draft_formal_quote_tax(
    formal_quote_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> OperationsTaxCalculationRead:
    require_pricing_inventory_write(db, user=current_user)
    formal_quote = db.scalar(
        select(FormalQuote)
        .options(
            selectinload(FormalQuote.items),
            selectinload(FormalQuote.charges),
        )
        .where(FormalQuote.id == formal_quote_id)
    )
    if formal_quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formal quote not found.",
        )

    try:
        calculation = calculate_formal_quote_tax(
            db,
            formal_quote=formal_quote,
            actor_user_id=current_user.id,
        )
    except TaxAutomationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    db.commit()
    db.refresh(calculation)
    return operations_tax_calculation_read(calculation)


@router.post(
    "/formal-quotes/{formal_quote_id}/staff-review/complete",
    response_model=OperationsFormalQuoteRead,
)
def complete_quote_staff_review(
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

    complete_formal_quote_staff_review(
        db,
        formal_quote=formal_quote,
        actor_user=current_user,
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

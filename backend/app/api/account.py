import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
)
from app.models.catalog import Product, ProductDocument
from app.models.customer import (
    CustomerAddress,
    CustomerCommunicationPreferences,
    CustomerEquipment,
    CustomerProfile,
)
from app.models.quote import (
    FormalQuote,
    FormalQuoteStatus,
    QuoteRequest,
)
from app.schemas.account import (
    AddressCreate,
    AddressRead,
    CommunicationPreferencesRead,
    CommunicationPreferencesUpdate,
    CustomerEquipmentDocumentRead,
    CustomerEquipmentRead,
    CustomerFormalQuoteItemRead,
    CustomerFormalQuoteRead,
    CustomerProfileRead,
    CustomerProfileUpdate,
    CustomerRequestRead,
)
from app.services.audit import (
    record_audit_event,
)
from app.services.formal_quotes import approve_formal_quote
from app.services.quote_orders import create_order_from_approved_quote

router = APIRouter(
    prefix="/account",
    tags=["account"],
)


def address_read(
    address: CustomerAddress,
) -> AddressRead:
    return AddressRead(
        id=str(address.id),
        label=address.label,
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        region_code=address.region_code,
        postal_code=address.postal_code,
        country_code=address.country_code,
        is_default_shipping=(address.is_default_shipping),
        is_default_billing=(address.is_default_billing),
    )


@router.get(
    "/profile",
    response_model=CustomerProfileRead,
)
def get_profile(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CustomerProfileRead:
    profile = db.get(
        CustomerProfile,
        current_user.id,
    )

    addresses = db.scalars(
        select(CustomerAddress)
        .where(CustomerAddress.user_id == current_user.id)
        .order_by(CustomerAddress.created_at)
    ).all()

    return CustomerProfileRead(
        email=current_user.email,
        first_name=(profile.first_name if profile is not None else None),
        last_name=(profile.last_name if profile is not None else None),
        phone=(profile.phone if profile is not None else None),
        addresses=[address_read(address) for address in addresses],
    )


@router.put(
    "/profile",
    response_model=CustomerProfileRead,
)
def update_profile(
    payload: CustomerProfileUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CustomerProfileRead:
    profile = db.get(
        CustomerProfile,
        current_user.id,
    )

    if profile is None:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)

    profile.first_name = payload.first_name
    profile.last_name = payload.last_name
    profile.phone = payload.phone

    record_audit_event(
        db,
        action="customer.profile_updated",
        entity_type="customer_profile",
        entity_id=str(current_user.id),
        actor_user_id=current_user.id,
    )

    db.commit()

    return get_profile(
        db,
        current_user,
    )


@router.post(
    "/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
)
def create_address(
    payload: AddressCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> AddressRead:
    if payload.is_default_shipping:
        for existing in db.scalars(
            select(CustomerAddress).where(
                CustomerAddress.user_id == current_user.id,
                CustomerAddress.is_default_shipping.is_(True),
            )
        ):
            existing.is_default_shipping = False

    if payload.is_default_billing:
        for existing in db.scalars(
            select(CustomerAddress).where(
                CustomerAddress.user_id == current_user.id,
                CustomerAddress.is_default_billing.is_(True),
            )
        ):
            existing.is_default_billing = False

    address = CustomerAddress(
        user_id=current_user.id,
        **payload.model_dump(),
    )

    db.add(address)
    db.flush()

    record_audit_event(
        db,
        action="customer.address_created",
        entity_type="customer_address",
        entity_id=str(address.id),
        actor_user_id=current_user.id,
    )

    db.commit()

    return address_read(address)


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_address(
    address_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> None:
    address = db.scalar(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.user_id == current_user.id,
        )
    )

    if address is None:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="Address not found.",
        )

    record_audit_event(
        db,
        action="customer.address_deleted",
        entity_type="customer_address",
        entity_id=str(address.id),
        actor_user_id=current_user.id,
    )

    db.delete(address)
    db.commit()


def communication_preferences_read(
    preferences: CustomerCommunicationPreferences | None,
) -> CommunicationPreferencesRead:
    if preferences is None:
        return CommunicationPreferencesRead()

    return CommunicationPreferencesRead(
        filter_replacement_reminders=preferences.filter_replacement_reminders,
        softener_check_reminders=preferences.softener_check_reminders,
        uv_service_reminders=preferences.uv_service_reminders,
        annual_system_check_reminders=preferences.annual_system_check_reminders,
        product_specific_reminders=preferences.product_specific_reminders,
        post_purchase_followup=preferences.post_purchase_followup,
        post_installation_followup=preferences.post_installation_followup,
    )


@router.get(
    "/communication-preferences",
    response_model=CommunicationPreferencesRead,
)
def get_communication_preferences(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CommunicationPreferencesRead:
    return communication_preferences_read(
        db.get(CustomerCommunicationPreferences, current_user.id)
    )


@router.put(
    "/communication-preferences",
    response_model=CommunicationPreferencesRead,
)
def update_communication_preferences(
    payload: CommunicationPreferencesUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CommunicationPreferencesRead:
    preferences = db.get(
        CustomerCommunicationPreferences,
        current_user.id,
    )

    if preferences is None:
        preferences = CustomerCommunicationPreferences(user_id=current_user.id)
        db.add(preferences)

    for field, value in payload.model_dump().items():
        setattr(preferences, field, value)

    record_audit_event(
        db,
        action="customer.communication_preferences_updated",
        entity_type="customer_communication_preferences",
        entity_id=str(current_user.id),
        actor_user_id=current_user.id,
        metadata={
            "enabled_count": sum(payload.model_dump().values()),
        },
    )

    db.commit()
    db.refresh(preferences)

    return communication_preferences_read(preferences)


@router.get(
    "/equipment",
    response_model=list[CustomerEquipmentRead],
)
def get_customer_equipment(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[CustomerEquipmentRead]:
    rows = db.scalars(
        select(CustomerEquipment)
        .where(
            CustomerEquipment.user_id == current_user.id,
            CustomerEquipment.active.is_(True),
        )
        .order_by(
            CustomerEquipment.installed_on.desc().nullslast(),
            CustomerEquipment.created_at.desc(),
        )
    ).all()

    results: list[CustomerEquipmentRead] = []
    for equipment in rows:
        product = (
            db.get(Product, equipment.product_id)
            if equipment.product_id is not None
            else None
        )
        documents = []
        if product is not None:
            documents = db.scalars(
                select(ProductDocument)
                .where(
                    ProductDocument.product_id == product.id,
                    ProductDocument.active.is_(True),
                    ProductDocument.public.is_(True),
                )
                .order_by(ProductDocument.document_type, ProductDocument.title)
            ).all()
        results.append(
            CustomerEquipmentRead(
                id=str(equipment.id),
                product_id=str(equipment.product_id) if equipment.product_id is not None else None,
                product_name=equipment.name_snapshot,
                product_family=product.product_family if product is not None else None,
                system_type=product.system_type if product is not None else None,
                sku=equipment.sku_snapshot,
                variant_name=equipment.variant_snapshot,
                serial_number=equipment.serial_number,
                location_label=equipment.location_label,
                installed_on=equipment.installed_on.isoformat() if equipment.installed_on else None,
                last_service_on=(
                    equipment.last_service_on.isoformat()
                    if equipment.last_service_on
                    else None
                ),
                next_service_due_on=(
                    equipment.next_service_due_on.isoformat()
                    if equipment.next_service_due_on
                    else None
                ),
                documents=[
                    CustomerEquipmentDocumentRead(
                        title=document.title,
                        document_type=document.document_type.value,
                        path=document.storage_path,
                        content_type=document.content_type,
                        version=document.version,
                    )
                    for document in documents
                ],
            )
        )
    return results


@router.get(
    "/requests",
    response_model=list[CustomerRequestRead],
)
def get_customer_requests(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[CustomerRequestRead]:
    rows = db.execute(
        select(QuoteRequest, Product.name)
        .outerjoin(Product, Product.id == QuoteRequest.product_id)
        .where(QuoteRequest.user_id == current_user.id)
        .order_by(QuoteRequest.created_at.desc())
    ).all()

    results: list[CustomerRequestRead] = []

    for quote, product_name in rows:
        decision = quote.recommendation_decision or {}
        results.append(
            CustomerRequestRead(
                id=str(quote.id),
                status=quote.status.value,
                product_name=product_name,
                created_at=quote.created_at.isoformat(),
                recommendation_title=(
                    str(decision.get("title"))
                    if decision.get("title")
                    else None
                ),
                human_review=bool(decision.get("human_review", False)),
                requires_third_party_lab=bool(
                    decision.get("requires_third_party_lab", False)
                ),
            )
        )

    return results


def customer_formal_quote_read(
    formal_quote: FormalQuote,
) -> CustomerFormalQuoteRead:
    return CustomerFormalQuoteRead(
        id=str(formal_quote.id),
        request_id=str(formal_quote.quote_request_id),
        revision_number=formal_quote.revision_number,
        status=formal_quote.status.value,
        currency=formal_quote.currency,
        subtotal_amount_minor=formal_quote.subtotal_amount_minor,
        customer_note=formal_quote.customer_note,
        presented_at=(
            formal_quote.presented_at.isoformat()
            if formal_quote.presented_at is not None
            else None
        ),
        approved_at=(
            formal_quote.approved_at.isoformat()
            if formal_quote.approved_at is not None
            else None
        ),
        created_at=formal_quote.created_at.isoformat(),
        items=[
            CustomerFormalQuoteItemRead(
                sku=item.sku_snapshot,
                name=item.name_snapshot,
                quantity=item.quantity,
                unit_amount_minor=item.unit_amount_minor,
                line_total_minor=item.line_total_minor,
                currency=item.currency,
                estimated_lead_time=item.estimated_lead_time_snapshot,
            )
            for item in formal_quote.items
        ],
    )


@router.get(
    "/quotes",
    response_model=list[CustomerFormalQuoteRead],
)
def get_customer_formal_quotes(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[CustomerFormalQuoteRead]:
    rows = db.scalars(
        select(FormalQuote)
        .options(selectinload(FormalQuote.items))
        .where(
            FormalQuote.customer_user_id == current_user.id,
            FormalQuote.status.in_(
                (
                    FormalQuoteStatus.presented,
                    FormalQuoteStatus.approved,
                    FormalQuoteStatus.superseded,
                )
            ),
        )
        .order_by(
            FormalQuote.created_at.desc(),
            FormalQuote.revision_number.desc(),
        )
    ).unique().all()

    # The relationship is loaded while the request-scoped session is open.
    return [customer_formal_quote_read(row) for row in rows]


@router.post(
    "/quotes/{formal_quote_id}/approve",
    response_model=CustomerFormalQuoteRead,
)
def approve_customer_formal_quote(
    formal_quote_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CustomerFormalQuoteRead:
    formal_quote = db.get(FormalQuote, formal_quote_id)
    if formal_quote is None or formal_quote.customer_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found.",
        )

    approve_formal_quote(
        db,
        formal_quote=formal_quote,
        customer_user=current_user,
    )
    create_order_from_approved_quote(
        db,
        formal_quote_id=formal_quote.id,
        customer_user=current_user,
    )
    db.commit()
    db.refresh(formal_quote)
    return customer_formal_quote_read(formal_quote)

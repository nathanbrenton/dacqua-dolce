import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import CurrentUser, DatabaseSession
from app.models.audit import AuditEvent
from app.models.catalog import Product, ProductInventory, ProductPrice
from app.models.commerce import (
    Order,
    OrderItem,
)
from app.models.communications import (
    CommunicationAttachment,
    CommunicationMessage,
    CommunicationRecipient,
    CommunicationThread,
)
from app.models.customer import (
    CustomerAddress,
    CustomerProfile,
)
from app.models.email import EmailDelivery, EmailDeliveryStatus
from app.models.identity import (
    RoleName,
    User,
    UserRole,
)
from app.models.quote import QuoteRequest, QuoteRequestStatus
from app.schemas.operations import (
    InventoryUpdateRequest,
    OperationsAuditEventRead,
    OperationsCommunicationAttachmentRead,
    OperationsCommunicationMessageRead,
    OperationsCommunicationRead,
    OperationsCommunicationRecipientRead,
    OperationsCommunicationThreadDetailRead,
    OperationsCommunicationThreadRead,
    OperationsCustomerAddressRead,
    OperationsCustomerRead,
    OperationsInventoryRead,
    OperationsOrderCustomerRead,
    OperationsOrderItemRead,
    OperationsOrderRead,
    OperationsPricingRead,
    OperationsProductRead,
    OperationsQuoteRead,
    OperationsSummaryRead,
    PricingUpdateRequest,
    QuoteNotesUpdate,
    QuoteStatusUpdate,
)
from app.services.audit import record_audit_event
from app.services.commerce import (
    active_reserved_quantity,
)
from app.services.operations_access import (
    require_operations,
    require_privileged_operations,
)
from app.services.pricing import select_effective_price

router = APIRouter(prefix="/operations", tags=["operations"])


def product_name_for_quote(
    db: DatabaseSession,
    product_id: uuid.UUID | None,
) -> str | None:
    if product_id is None:
        return None

    return db.scalar(select(Product.name).where(Product.id == product_id))


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
        internal_notes=quote.internal_notes,
        status=quote.status.value,
        created_at=quote.created_at.isoformat(),
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
        active_products=int(active_products),
        failed_email_deliveries=int(failed_email_deliveries),
    )


def operations_audit_event_read(
    *,
    event: AuditEvent,
) -> OperationsAuditEventRead:
    return OperationsAuditEventRead(
        id=str(event.id),
        actor_user_id=(
            str(event.actor_user_id)
            if event.actor_user_id is not None
            else None
        ),
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        environment=event.environment,
        created_at=event.created_at.isoformat(),
    )


@router.get(
    "/audit-events",
    response_model=list[OperationsAuditEventRead],
)
def list_audit_events(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsAuditEventRead]:
    require_privileged_operations(
        db,
        user=current_user,
    )

    events = db.scalars(
        select(AuditEvent)
        .order_by(
            AuditEvent.created_at.desc(),
            AuditEvent.id,
        )
        .limit(500)
    ).all()

    return [
        operations_audit_event_read(
            event=event,
        )
        for event in events
    ]


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

    return OperationsCommunicationThreadDetailRead(
        **summary.model_dump(),
        messages=_communication_message_reads(
            db,
            messages=messages,
        ),
    )


@router.get("/quotes", response_model=list[OperationsQuoteRead])
def list_quotes(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[OperationsQuoteRead]:
    require_operations(db, user=current_user)

    quotes = db.scalars(
        select(QuoteRequest).order_by(QuoteRequest.created_at.desc()).limit(200)
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

    return OperationsOrderRead(
        id=str(order.id),
        status=order.status.value,
        total_amount_minor=order.total_amount_minor,
        currency=order.currency,
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
            )
            for item in items
        ],
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
        active=product.active,
        online_sale_approved=(
            product.online_sale_approved
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
        ),
        inventory=OperationsInventoryRead(
            status=(inventory.inventory_status.value if inventory is not None else "not_tracked"),
            quantity_on_hand=(inventory.quantity_on_hand if inventory is not None else 0),
            quantity_reserved=reserved_quantity,
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
        )
        .order_by(Product.name)
    ).all()

    return [operations_product_read(db, product=product) for product in products]


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
    require_privileged_operations(db, user=current_user)

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
    require_operations(db, user=current_user)

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
            inventory_status=payload.status,
            quantity_on_hand=(
                payload.quantity_on_hand
            ),
        )
        db.add(inventory)
    else:
        inventory.inventory_status = (
            payload.status
        )
        inventory.quantity_on_hand = (
            payload.quantity_on_hand
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

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import CurrentUser, DatabaseSession
from app.models.catalog import Product, ProductInventory, ProductPrice
from app.models.email import EmailDelivery, EmailDeliveryStatus
from app.models.quote import QuoteRequest, QuoteRequestStatus
from app.schemas.operations import (
    InventoryUpdateRequest,
    OperationsInventoryRead,
    OperationsPricingRead,
    OperationsProductRead,
    OperationsQuoteRead,
    OperationsSummaryRead,
    PricingUpdateRequest,
    QuoteNotesUpdate,
    QuoteStatusUpdate,
)
from app.services.audit import record_audit_event
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

    return OperationsProductRead(
        id=str(product.id),
        sku=product.sku,
        name=product.name,
        category=product.category.name,
        manufacturer=product.manufacturer.name,
        active=product.active,
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
            quantity_reserved=(inventory.quantity_reserved if inventory is not None else 0),
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
        select(ProductInventory).where(
            ProductInventory.product_id == product.id,
            ProductInventory.variant_id.is_(None),
        )
    )

    if inventory is None:
        inventory = ProductInventory(
            product_id=product.id,
            variant_id=None,
            inventory_status=payload.status,
            quantity_on_hand=payload.quantity_on_hand,
            quantity_reserved=payload.quantity_reserved,
        )
        db.add(inventory)
    else:
        inventory.inventory_status = payload.status
        inventory.quantity_on_hand = payload.quantity_on_hand
        inventory.quantity_reserved = payload.quantity_reserved

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
            "quantity_on_hand": payload.quantity_on_hand,
            "quantity_reserved": payload.quantity_reserved,
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

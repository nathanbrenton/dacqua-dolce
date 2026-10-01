import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import (
    PricingPolicyMode,
    Product,
    ProductInventory,
    ProductPrice,
    ProductVariant,
)
from app.models.identity import RoleName, User, UserRole, UserStatus
from app.models.quote import (
    CommercialChargeKind,
    FormalQuote,
    FormalQuoteCharge,
    FormalQuoteItem,
    FormalQuoteStatus,
    QuoteRequest,
    QuoteRequestStatus,
)
from app.services.audit import record_audit_event
from app.services.policies import snapshot_quote_policies
from app.services.pricing import select_effective_price

FORMAL_QUOTE_VALIDITY_DAYS = 30


@dataclass(frozen=True)
class FormalQuoteChargeInput:
    kind: CommercialChargeKind
    label: str
    amount_minor: int


@dataclass(frozen=True)
class FormalQuoteLineInput:
    product_id: object
    variant_id: object | None
    quantity: int
    unit_amount_minor: int | None


def _customer_account_for_request(
    db: Session,
    request: QuoteRequest,
) -> User | None:
    if request.user_id is not None:
        user = db.get(User, request.user_id)
        if user is not None and user.status == UserStatus.active:
            return user

    return db.scalar(
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .where(
            User.email == request.email,
            User.status == UserStatus.active,
            UserRole.role == RoleName.customer,
        )
    )


def _inventory_for_line(
    db: Session,
    *,
    product_id: object,
    variant_id: object | None,
) -> ProductInventory | None:
    if variant_id is not None:
        row = db.scalar(
            select(ProductInventory).where(
                ProductInventory.product_id == product_id,
                ProductInventory.variant_id == variant_id,
            )
        )
        if row is not None:
            return row

    return db.scalar(
        select(ProductInventory).where(
            ProductInventory.product_id == product_id,
            ProductInventory.variant_id.is_(None),
        )
    )


def _line_snapshot(
    db: Session,
    *,
    line: FormalQuoteLineInput,
    allow_catalog_price_override: bool,
) -> tuple[FormalQuoteItem, str]:
    product = db.get(Product, line.product_id)
    if product is None or not product.active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quote line product is unavailable.",
        )

    variant: ProductVariant | None = None
    if line.variant_id is not None:
        variant = db.get(ProductVariant, line.variant_id)
        if (
            variant is None
            or not variant.active
            or variant.product_id != product.id
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quote line variant is unavailable for that product.",
            )

    prices = list(
        db.scalars(
            select(ProductPrice).where(
                ProductPrice.product_id == product.id,
            )
        ).all()
    )
    effective_price = select_effective_price(
        prices,
        variant_id=(variant.id if variant is not None else None),
    )
    if effective_price is None and variant is not None:
        effective_price = select_effective_price(
            prices,
            variant_id=None,
        )

    catalog_amount = (
        effective_price.amount_minor
        if effective_price is not None
        else None
    )
    requested_amount = line.unit_amount_minor

    if catalog_amount is not None:
        if requested_amount is None:
            unit_amount = catalog_amount
        elif requested_amount != catalog_amount:
            if not allow_catalog_price_override:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Administrator authorization is required to override "
                        "the current catalog price."
                    ),
                )
            unit_amount = requested_amount
        else:
            unit_amount = requested_amount
    else:
        if requested_amount is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Enter a quoted unit price for products without an "
                    "authoritative catalog amount."
                ),
            )
        unit_amount = requested_amount

    currency = (
        effective_price.currency
        if effective_price is not None
        else "USD"
    ).upper()
    pricing_mode = (
        effective_price.pricing_policy_mode.value
        if effective_price is not None
        else PricingPolicyMode.NO_ONLINE_PRICE.value
    )
    inventory = _inventory_for_line(
        db,
        product_id=product.id,
        variant_id=(variant.id if variant is not None else None),
    )

    name_snapshot = product.name
    sku_snapshot = product.sku
    if variant is not None:
        name_snapshot = f"{product.name} — {variant.display_name}"
        sku_snapshot = variant.sku

    item = FormalQuoteItem(
        product_id=product.id,
        variant_id=(variant.id if variant is not None else None),
        sku_snapshot=sku_snapshot,
        name_snapshot=name_snapshot,
        quantity=line.quantity,
        unit_amount_minor=unit_amount,
        line_total_minor=unit_amount * line.quantity,
        currency=currency,
        pricing_policy_mode_snapshot=pricing_mode,
        estimated_lead_time_snapshot=(
            inventory.estimated_lead_time
            if inventory is not None
            else None
        ),
    )
    return item, currency


def create_formal_quote_revision(
    db: Session,
    *,
    quote_request: QuoteRequest,
    lines: list[FormalQuoteLineInput],
    charges: list[FormalQuoteChargeInput],
    delivery_address_snapshot: dict[str, object],
    billing_address_snapshot: dict[str, object],
    customer_note: str | None,
    actor_user: User,
    actor_roles: set[RoleName],
) -> FormalQuote:
    approved = db.scalar(
        select(FormalQuote.id).where(
            FormalQuote.quote_request_id == quote_request.id,
            FormalQuote.status == FormalQuoteStatus.approved,
        )
    )
    if approved is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This request already has an approved quote. "
                "Create the next commercial workflow before revising it."
            ),
        )

    for draft in db.scalars(
        select(FormalQuote).where(
            FormalQuote.quote_request_id == quote_request.id,
            FormalQuote.status == FormalQuoteStatus.draft,
        )
    ):
        draft.status = FormalQuoteStatus.superseded

    revision_number = (
        db.scalar(
            select(func.max(FormalQuote.revision_number)).where(
                FormalQuote.quote_request_id == quote_request.id,
            )
        )
        or 0
    ) + 1

    allow_override = not actor_roles.isdisjoint(
        {RoleName.administrator, RoleName.developer}
    )
    items: list[FormalQuoteItem] = []
    currencies: set[str] = set()

    for sort_order, line in enumerate(lines):
        item, currency = _line_snapshot(
            db,
            line=line,
            allow_catalog_price_override=allow_override,
        )
        item.sort_order = sort_order
        items.append(item)
        currencies.add(currency)

    if len(currencies) != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="All formal quote lines must use the same currency.",
        )

    subtotal = sum(item.line_total_minor for item in items)
    charge_rows: list[FormalQuoteCharge] = []
    for sort_order, charge in enumerate(charges):
        label = charge.label.strip()
        if not label:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Commercial charge labels cannot be blank.",
            )

        positive_kinds = {
            CommercialChargeKind.shipping,
            CommercialChargeKind.tax,
            CommercialChargeKind.installation,
            CommercialChargeKind.other_charge,
        }
        credit_kinds = {
            CommercialChargeKind.discount,
            CommercialChargeKind.other_credit,
        }
        if charge.kind in positive_kinds and charge.amount_minor <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Commercial charges must be greater than zero.",
            )
        if charge.kind in credit_kinds and charge.amount_minor >= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Discounts and credits must be negative amounts.",
            )

        charge_rows.append(
            FormalQuoteCharge(
                kind=charge.kind.value,
                label=label,
                amount_minor=charge.amount_minor,
                sort_order=sort_order,
            )
        )

    charges_total = sum(charge.amount_minor for charge in charge_rows)
    total = subtotal + charges_total
    if total < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Commercial credits cannot reduce the quote total below zero.",
        )

    formal_quote = FormalQuote(
        quote_request_id=quote_request.id,
        revision_number=revision_number,
        status=FormalQuoteStatus.draft,
        customer_user_id=quote_request.user_id,
        authored_by_user_id=actor_user.id,
        currency=currencies.pop(),
        subtotal_amount_minor=subtotal,
        charges_amount_minor=charges_total,
        total_amount_minor=total,
        delivery_address_snapshot=delivery_address_snapshot,
        billing_address_snapshot=billing_address_snapshot,
        customer_note=customer_note,
        items=items,
        charges=charge_rows,
    )
    db.add(formal_quote)
    db.flush()

    record_audit_event(
        db,
        action="formal_quote.created",
        entity_type="formal_quote",
        entity_id=str(formal_quote.id),
        actor_user_id=actor_user.id,
        metadata={
            "quote_request_id": str(quote_request.id),
            "revision_number": revision_number,
            "line_count": len(items),
            "subtotal_amount_minor": subtotal,
            "charges_amount_minor": charges_total,
            "total_amount_minor": total,
            "charge_count": len(charge_rows),
            "currency": formal_quote.currency,
        },
    )

    return formal_quote


def present_formal_quote(
    db: Session,
    *,
    formal_quote: FormalQuote,
    actor_user: User,
) -> FormalQuote:
    if formal_quote.status != FormalQuoteStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a draft quote can be presented to a customer.",
        )

    request = db.get(QuoteRequest, formal_quote.quote_request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer request not found.",
        )

    approved = db.scalar(
        select(FormalQuote.id).where(
            FormalQuote.quote_request_id == request.id,
            FormalQuote.status == FormalQuoteStatus.approved,
        )
    )
    if approved is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An approved quote already locks this request's commercial terms.",
        )

    customer = _customer_account_for_request(db, request)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A customer account using the request email is required "
                "before this quote can be presented for approval."
            ),
        )

    if formal_quote.delivery_address_snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A delivery/service address snapshot is required before presentation.",
        )
    if formal_quote.billing_address_snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A billing address snapshot is required before presentation.",
        )
    if formal_quote.total_amount_minor <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A presented quote must have a positive final total.",
        )

    policy_snapshots = snapshot_quote_policies(
        db,
        formal_quote=formal_quote,
    )

    for previous in db.scalars(
        select(FormalQuote).where(
            FormalQuote.quote_request_id == request.id,
            FormalQuote.status == FormalQuoteStatus.presented,
            FormalQuote.id != formal_quote.id,
        )
    ):
        previous.status = FormalQuoteStatus.superseded

    now = datetime.now(UTC)
    formal_quote.customer_user_id = customer.id
    formal_quote.status = FormalQuoteStatus.presented
    formal_quote.presented_at = now
    formal_quote.expires_at = now + timedelta(
        days=FORMAL_QUOTE_VALIDITY_DAYS
    )
    request.user_id = customer.id
    request.status = QuoteRequestStatus.quoted

    record_audit_event(
        db,
        action="formal_quote.presented",
        entity_type="formal_quote",
        entity_id=str(formal_quote.id),
        actor_user_id=actor_user.id,
        metadata={
            "quote_request_id": str(request.id),
            "revision_number": formal_quote.revision_number,
            "expires_at": formal_quote.expires_at.isoformat(),
            "policy_versions": {
                snapshot.kind.value: snapshot.version_snapshot
                for snapshot in policy_snapshots
            },
        },
    )
    return formal_quote


def approve_formal_quote(
    db: Session,
    *,
    formal_quote: FormalQuote,
    customer_user: User,
    acknowledged_policy_snapshot_ids: set[uuid.UUID],
) -> FormalQuote:
    if formal_quote.customer_user_id != customer_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found.",
        )
    if formal_quote.status != FormalQuoteStatus.presented:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a currently presented quote can be approved.",
        )

    now = datetime.now(UTC)
    expires_at = getattr(formal_quote, "expires_at", None)
    if expires_at is not None and expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This formal quote has expired. "
                "Request a current quote before approval."
            ),
        )

    expected_policy_ids = {
        snapshot.id
        for snapshot in formal_quote.policy_snapshots
    }
    if not expected_policy_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This quote does not contain the required policy snapshots.",
        )
    if acknowledged_policy_snapshot_ids != expected_policy_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review and acknowledge every policy version attached to this quote.",
        )

    for draft in db.scalars(
        select(FormalQuote).where(
            FormalQuote.quote_request_id == formal_quote.quote_request_id,
            FormalQuote.status == FormalQuoteStatus.draft,
            FormalQuote.id != formal_quote.id,
        )
    ):
        draft.status = FormalQuoteStatus.superseded

    formal_quote.status = FormalQuoteStatus.approved
    formal_quote.approved_at = now
    formal_quote.approved_by_user_id = customer_user.id

    record_audit_event(
        db,
        action="formal_quote.approved",
        entity_type="formal_quote",
        entity_id=str(formal_quote.id),
        actor_user_id=customer_user.id,
        metadata={
            "quote_request_id": str(formal_quote.quote_request_id),
            "revision_number": formal_quote.revision_number,
            "subtotal_amount_minor": formal_quote.subtotal_amount_minor,
            "charges_amount_minor": formal_quote.charges_amount_minor,
            "total_amount_minor": formal_quote.total_amount_minor,
            "currency": formal_quote.currency,
            "policy_acknowledgments": [
                {
                    "kind": snapshot.kind.value,
                    "version": snapshot.version_snapshot,
                    "content_sha256": snapshot.content_sha256,
                    "structured_terms_sha256": getattr(
                        snapshot,
                        "structured_terms_sha256",
                        None,
                    ),
                }
                for snapshot in formal_quote.policy_snapshots
            ],
        },
    )
    return formal_quote

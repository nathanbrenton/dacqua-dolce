from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.tax_config import TaxConfigurationError, load_tax_runtime_settings
from app.models.commerce import (
    Order,
    OrderCharge,
    OrderItem,
    OrderStatus,
)
from app.models.quote import (
    CommercialChargeKind,
    FormalQuote,
    FormalQuoteCharge,
    FormalQuoteStatus,
)
from app.models.tax import (
    ProductTaxClassification,
    TaxCalculation,
    TaxTransaction,
)
from app.services.audit import record_audit_event
from app.services.stripe_tax import StripeTaxError, StripeTaxSandboxAdapter
from app.services.tax_provider import (
    TaxAddress,
    TaxCalculationRequest,
    TaxCalculationResult,
    TaxLineItem,
    TaxProviderAdapter,
)


class TaxAutomationError(ValueError):
    pass


class TaxCheckoutReadinessError(TaxAutomationError):
    pass


TAX_PROVIDER = "stripe_tax"
_UNSUPPORTED_AUTOMATED_TAX_CHARGES = {
    CommercialChargeKind.shipping_insurance.value,
    CommercialChargeKind.installation.value,
    CommercialChargeKind.discount.value,
    CommercialChargeKind.other_charge.value,
    CommercialChargeKind.other_credit.value,
}


def configured_tax_provider() -> TaxProviderAdapter:
    try:
        settings = load_tax_runtime_settings()
    except TaxConfigurationError as exc:
        raise TaxAutomationError(str(exc)) from exc

    if settings.mode != "stripe_test" or settings.stripe_secret_key is None:
        raise TaxAutomationError(
            "Automated tax is not configured. PT44 supports Stripe Tax "
            "test mode only until production tax commissioning is complete."
        )

    try:
        return StripeTaxSandboxAdapter(
            secret_key=settings.stripe_secret_key,
        )
    except StripeTaxError as exc:
        raise TaxAutomationError(str(exc)) from exc


def _tax_address(snapshot: dict[str, object] | None) -> TaxAddress:
    if snapshot is None:
        raise TaxAutomationError(
            "A delivery address is required for authoritative tax calculation."
        )

    def required(key: str) -> str:
        value = snapshot.get(key)
        if not isinstance(value, str) or not value.strip():
            raise TaxAutomationError(
                "The delivery address is incomplete for tax calculation."
            )
        return value.strip()

    line2 = snapshot.get("line2")
    return TaxAddress(
        line1=required("line1"),
        line2=(
            line2.strip()
            if isinstance(line2, str) and line2.strip()
            else None
        ),
        city=required("city"),
        region_code=required("region_code").upper(),
        postal_code=required("postal_code"),
        country_code=required("country_code").upper(),
    )


def _classifications_for_products(
    db: Session,
    *,
    product_ids: set[uuid.UUID],
) -> dict[uuid.UUID, ProductTaxClassification]:
    if not product_ids:
        return {}

    rows = db.scalars(
        select(ProductTaxClassification).where(
            ProductTaxClassification.product_id.in_(product_ids),
            ProductTaxClassification.provider == TAX_PROVIDER,
            ProductTaxClassification.active.is_(True),
        )
    ).all()
    return {
        row.product_id: row
        for row in rows
    }


def _reject_unsupported_adjustments(charges: list[object]) -> None:
    unsupported = sorted(
        {
            str(charge.kind)
            for charge in charges
            if str(charge.kind) in _UNSUPPORTED_AUTOMATED_TAX_CHARGES
        }
    )
    if unsupported:
        raise TaxAutomationError(
            "Automated tax is intentionally blocked for quotes/orders containing "
            "commercial adjustment types whose taxability is not yet mapped: "
            + ", ".join(unsupported)
            + "."
        )


def _request_from_quote(
    db: Session,
    *,
    formal_quote: FormalQuote,
) -> TaxCalculationRequest:
    if formal_quote.status != FormalQuoteStatus.draft:
        raise TaxAutomationError(
            "Only a draft formal quote can receive a sandbox tax calculation."
        )

    _reject_unsupported_adjustments(list(formal_quote.charges))

    if any(item.product_id is None for item in formal_quote.items):
        raise TaxAutomationError(
            "Every formal quote line must retain a product identity for automated tax."
        )
    product_ids = {
        item.product_id
        for item in formal_quote.items
        if item.product_id is not None
    }

    classifications = _classifications_for_products(
        db,
        product_ids=product_ids,
    )
    missing = [
        item.sku_snapshot
        for item in formal_quote.items
        if item.product_id not in classifications
    ]
    if missing:
        raise TaxAutomationError(
            "Tax classification is missing for: " + ", ".join(sorted(missing))
        )

    shipping_amount = sum(
        charge.amount_minor
        for charge in formal_quote.charges
        if charge.kind == CommercialChargeKind.shipping.value
    )

    return TaxCalculationRequest(
        currency=formal_quote.currency,
        customer_address=_tax_address(formal_quote.delivery_address_snapshot),
        line_items=tuple(
            TaxLineItem(
                reference=item.sku_snapshot,
                amount_minor=item.line_total_minor,
                quantity=item.quantity,
                tax_code=classifications[item.product_id].tax_code,
            )
            for item in formal_quote.items
        ),
        shipping_amount_minor=shipping_amount,
        idempotency_key=f"formal-quote:{formal_quote.id}:tax:{uuid.uuid4().hex}",
    )


def _request_from_order(
    db: Session,
    *,
    order: Order,
    items: list[OrderItem],
    charges: list[OrderCharge],
) -> TaxCalculationRequest:
    if order.status != OrderStatus.awaiting_payment:
        raise TaxAutomationError(
            "Only an order awaiting payment can be recalculated for tax."
        )

    _reject_unsupported_adjustments(list(charges))

    if any(item.product_id is None for item in items):
        raise TaxAutomationError(
            "Every order line must retain a product identity for automated tax."
        )
    product_ids = {
        item.product_id
        for item in items
        if item.product_id is not None
    }

    classifications = _classifications_for_products(
        db,
        product_ids=product_ids,
    )
    missing = [
        item.sku_snapshot
        for item in items
        if item.product_id not in classifications
    ]
    if missing:
        raise TaxAutomationError(
            "Tax classification is missing for: " + ", ".join(sorted(missing))
        )

    shipping_amount = sum(
        charge.amount_minor
        for charge in charges
        if charge.kind == CommercialChargeKind.shipping.value
    )

    return TaxCalculationRequest(
        currency=order.currency,
        customer_address=_tax_address(order.delivery_address_snapshot),
        line_items=tuple(
            TaxLineItem(
                reference=item.sku_snapshot,
                amount_minor=item.line_total_minor,
                quantity=item.quantity,
                tax_code=classifications[item.product_id].tax_code,
            )
            for item in items
        ),
        shipping_amount_minor=shipping_amount,
        idempotency_key=f"order:{order.id}:tax:{uuid.uuid4().hex}",
    )


def _request_summary(
    request: TaxCalculationRequest,
) -> dict[str, object]:
    return {
        "currency": request.currency.upper(),
        "delivery_jurisdiction": {
            "country_code": request.customer_address.country_code,
            "region_code": request.customer_address.region_code,
            "postal_code": request.customer_address.postal_code,
        },
        "line_items": [
            {
                "reference": item.reference,
                "amount_minor": item.amount_minor,
                "quantity": item.quantity,
                "tax_code": item.tax_code,
            }
            for item in request.line_items
        ],
        "shipping_amount_minor": request.shipping_amount_minor,
    }


def _response_summary(
    result: TaxCalculationResult,
) -> dict[str, object]:
    return {
        "line_items": list(result.line_items),
        "tax_breakdown": list(result.tax_breakdown),
    }


def _supersede_existing(
    db: Session,
    *,
    formal_quote_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
) -> None:
    statement = select(TaxCalculation).where(
        TaxCalculation.superseded_at.is_(None),
        TaxCalculation.committed_at.is_(None),
    )
    if formal_quote_id is not None:
        statement = statement.where(
            TaxCalculation.formal_quote_id == formal_quote_id,
        )
    elif order_id is not None:
        statement = statement.where(
            TaxCalculation.order_id == order_id,
        )
    else:
        raise TaxAutomationError("Tax calculation context is required.")

    now = datetime.now(UTC)
    for prior in db.scalars(statement).all():
        prior.superseded_at = now


def _persist_calculation(
    db: Session,
    *,
    request: TaxCalculationRequest,
    result: TaxCalculationResult,
    formal_quote_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
) -> TaxCalculation:
    if result.livemode:
        raise TaxAutomationError(
            "PT44 refused to persist a live-mode tax calculation."
        )
    if result.currency.upper() != request.currency.upper():
        raise TaxAutomationError(
            "Tax provider currency does not match the commercial context."
        )

    _supersede_existing(
        db,
        formal_quote_id=formal_quote_id,
        order_id=order_id,
    )

    calculation = TaxCalculation(
        formal_quote_id=formal_quote_id,
        order_id=order_id,
        provider=result.provider,
        provider_calculation_id=result.provider_calculation_id,
        currency=result.currency.upper(),
        line_items_amount_minor=result.line_items_amount_minor,
        shipping_amount_minor=result.shipping_amount_minor,
        tax_amount_minor=result.tax_amount_minor,
        amount_total_minor=result.amount_total_minor,
        livemode=result.livemode,
        expires_at=result.expires_at,
        request_summary=_request_summary(request),
        response_summary=_response_summary(result),
    )
    db.add(calculation)
    db.flush()
    return calculation


def _apply_quote_tax(
    db: Session,
    *,
    formal_quote: FormalQuote,
    result: TaxCalculationResult,
) -> None:
    base_charges = [
        charge
        for charge in formal_quote.charges
        if charge.kind != CommercialChargeKind.tax.value
    ]
    for charge in list(formal_quote.charges):
        if charge.kind == CommercialChargeKind.tax.value:
            formal_quote.charges.remove(charge)
            db.delete(charge)

    if result.tax_amount_minor > 0:
        next_sort = (
            max(
                (charge.sort_order for charge in base_charges),
                default=-1,
            )
            + 1
        )
        formal_quote.charges.append(
            FormalQuoteCharge(
                kind=CommercialChargeKind.tax.value,
                label="Tax",
                amount_minor=result.tax_amount_minor,
                sort_order=next_sort,
            )
        )

    formal_quote.charges_amount_minor = sum(
        charge.amount_minor
        for charge in formal_quote.charges
    )
    formal_quote.total_amount_minor = (
        formal_quote.subtotal_amount_minor
        + formal_quote.charges_amount_minor
    )


def _apply_order_tax(
    db: Session,
    *,
    order: Order,
    charges: list[OrderCharge],
    result: TaxCalculationResult,
) -> None:
    base_charges = [
        charge
        for charge in charges
        if charge.kind != CommercialChargeKind.tax.value
    ]
    for charge in charges:
        if charge.kind == CommercialChargeKind.tax.value:
            db.delete(charge)

    if result.tax_amount_minor > 0:
        next_sort = (
            max(
                (charge.sort_order for charge in base_charges),
                default=-1,
            )
            + 1
        )
        db.add(
            OrderCharge(
                order_id=order.id,
                kind=CommercialChargeKind.tax.value,
                label="Tax",
                amount_minor=result.tax_amount_minor,
                sort_order=next_sort,
            )
        )

    base_charge_total = sum(
        charge.amount_minor
        for charge in base_charges
    )
    order.charges_amount_minor = (
        base_charge_total
        + result.tax_amount_minor
    )
    order.total_amount_minor = (
        order.subtotal_amount_minor
        + order.charges_amount_minor
    )


def calculate_formal_quote_tax(
    db: Session,
    *,
    formal_quote: FormalQuote,
    actor_user_id: uuid.UUID,
    provider: TaxProviderAdapter | None = None,
) -> TaxCalculation:
    request = _request_from_quote(
        db,
        formal_quote=formal_quote,
    )
    adapter = provider or configured_tax_provider()

    try:
        result = adapter.calculate(request)
    except (StripeTaxError, ValueError) as exc:
        raise TaxAutomationError(str(exc)) from exc

    expected_base = (
        formal_quote.subtotal_amount_minor
        + request.shipping_amount_minor
    )
    if (
        result.line_items_amount_minor != formal_quote.subtotal_amount_minor
        or result.shipping_amount_minor != request.shipping_amount_minor
        or result.amount_total_minor
        != expected_base + result.tax_amount_minor
    ):
        raise TaxAutomationError(
            "Tax calculation does not reconcile to the draft quote."
        )

    _apply_quote_tax(
        db,
        formal_quote=formal_quote,
        result=result,
    )
    calculation = _persist_calculation(
        db,
        request=request,
        result=result,
        formal_quote_id=formal_quote.id,
    )

    record_audit_event(
        db,
        action="tax.formal_quote_calculated",
        entity_type="formal_quote",
        entity_id=str(formal_quote.id),
        actor_user_id=actor_user_id,
        metadata={
            "provider": result.provider,
            "provider_calculation_id": result.provider_calculation_id,
            "tax_amount_minor": result.tax_amount_minor,
            "amount_total_minor": formal_quote.total_amount_minor,
            "livemode": result.livemode,
        },
    )
    db.flush()
    return calculation


def calculate_order_tax(
    db: Session,
    *,
    order: Order,
    actor_user_id: uuid.UUID,
    provider: TaxProviderAdapter | None = None,
) -> TaxCalculation:
    items = list(
        db.scalars(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.created_at, OrderItem.id)
        ).all()
    )
    charges = list(
        db.scalars(
            select(OrderCharge)
            .where(OrderCharge.order_id == order.id)
            .order_by(OrderCharge.sort_order, OrderCharge.created_at)
        ).all()
    )
    if not items:
        raise TaxAutomationError(
            "Order does not contain taxable line items."
        )

    request = _request_from_order(
        db,
        order=order,
        items=items,
        charges=charges,
    )
    adapter = provider or configured_tax_provider()

    try:
        result = adapter.calculate(request)
    except (StripeTaxError, ValueError) as exc:
        raise TaxAutomationError(str(exc)) from exc

    expected_line_amount = sum(item.line_total_minor for item in items)
    expected_base = expected_line_amount + request.shipping_amount_minor
    if (
        result.line_items_amount_minor != expected_line_amount
        or result.shipping_amount_minor != request.shipping_amount_minor
        or result.amount_total_minor
        != expected_base + result.tax_amount_minor
    ):
        raise TaxAutomationError(
            "Tax calculation does not reconcile to the order."
        )

    _apply_order_tax(
        db,
        order=order,
        charges=charges,
        result=result,
    )
    calculation = _persist_calculation(
        db,
        request=request,
        result=result,
        order_id=order.id,
    )

    record_audit_event(
        db,
        action="tax.order_calculated",
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=actor_user_id,
        metadata={
            "provider": result.provider,
            "provider_calculation_id": result.provider_calculation_id,
            "tax_amount_minor": result.tax_amount_minor,
            "amount_total_minor": order.total_amount_minor,
            "livemode": result.livemode,
        },
    )
    db.flush()
    return calculation


def current_order_tax_calculation(
    db: Session,
    *,
    order_id: uuid.UUID,
) -> TaxCalculation | None:
    return db.scalar(
        select(TaxCalculation)
        .where(
            TaxCalculation.order_id == order_id,
            TaxCalculation.superseded_at.is_(None),
        )
        .order_by(TaxCalculation.created_at.desc())
        .limit(1)
    )


def require_order_tax_ready(
    db: Session,
    *,
    order: Order,
    now: datetime | None = None,
) -> TaxCalculation:
    calculation = current_order_tax_calculation(
        db,
        order_id=order.id,
    )
    if calculation is None:
        raise TaxCheckoutReadinessError(
            "Authoritative automated tax must be recalculated before checkout."
        )
    if calculation.livemode:
        raise TaxCheckoutReadinessError(
            "PT44 checkout boundary refuses live tax evidence until "
            "production tax commissioning is explicitly completed."
        )
    if get_settings().is_production:
        raise TaxCheckoutReadinessError(
            "PT44 sandbox tax evidence cannot authorize production checkout. "
            "Complete live tax commissioning before enabling production payment."
        )
    current_time = now or datetime.now(UTC)
    if (
        calculation.expires_at is not None
        and calculation.expires_at <= current_time
    ):
        raise TaxCheckoutReadinessError(
            "The authoritative tax calculation has expired. Recalculate tax."
        )
    if calculation.committed_at is not None:
        raise TaxCheckoutReadinessError(
            "The tax calculation has already been committed to a transaction."
        )
    if calculation.amount_total_minor != order.total_amount_minor:
        raise TaxCheckoutReadinessError(
            "The order total no longer matches its authoritative tax calculation."
        )
    if calculation.currency.upper() != order.currency.upper():
        raise TaxCheckoutReadinessError(
            "The order currency no longer matches its authoritative tax calculation."
        )
    return calculation


def commit_paid_order_tax_transaction(
    db: Session,
    *,
    order: Order,
    provider: TaxProviderAdapter | None = None,
) -> TaxTransaction:
    if order.status not in {
        OrderStatus.paid,
        OrderStatus.processing,
        OrderStatus.shipped,
        OrderStatus.delivered,
    }:
        raise TaxAutomationError(
            "Tax liability can only be committed after verified payment."
        )

    existing = db.scalar(
        select(TaxTransaction).where(
            TaxTransaction.order_id == order.id,
        )
    )
    if existing is not None:
        return existing

    calculation = current_order_tax_calculation(
        db,
        order_id=order.id,
    )
    if calculation is None:
        raise TaxAutomationError(
            "Paid order is missing authoritative tax calculation evidence."
        )
    if calculation.livemode:
        raise TaxAutomationError(
            "PT44 does not commit live tax transactions."
        )
    if calculation.amount_total_minor != order.total_amount_minor:
        raise TaxAutomationError(
            "Paid order total does not match its tax calculation."
        )

    adapter = provider or configured_tax_provider()
    reference = f"dacqua-order:{order.id}"
    try:
        result = adapter.create_transaction_from_calculation(
            provider_calculation_id=calculation.provider_calculation_id,
            reference=reference,
            idempotency_key=f"order:{order.id}:tax-transaction",
        )
    except (StripeTaxError, ValueError) as exc:
        raise TaxAutomationError(str(exc)) from exc

    if result.livemode:
        raise TaxAutomationError(
            "PT44 refused to persist a live-mode tax transaction."
        )
    if (
        result.currency.upper() != order.currency.upper()
        or result.amount_total_minor != order.total_amount_minor
        or result.tax_amount_minor != calculation.tax_amount_minor
    ):
        raise TaxAutomationError(
            "Tax transaction does not reconcile to the paid order."
        )

    transaction = TaxTransaction(
        order_id=order.id,
        calculation_id=calculation.id,
        provider=result.provider,
        provider_transaction_id=result.provider_transaction_id,
        provider_reference=result.provider_reference,
        currency=result.currency.upper(),
        tax_amount_minor=result.tax_amount_minor,
        amount_total_minor=result.amount_total_minor,
        livemode=result.livemode,
        response_summary=result.response_summary,
    )
    db.add(transaction)
    calculation.committed_at = datetime.now(UTC)
    db.flush()
    return transaction

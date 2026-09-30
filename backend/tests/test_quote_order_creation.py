import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.commerce import Order, OrderCharge, OrderStatus
from app.models.quote import (
    FormalQuote,
    FormalQuoteCharge,
    FormalQuoteItem,
    FormalQuoteStatus,
)
from app.services.quote_orders import create_order_from_approved_quote


class QuoteOrderDatabase:
    def __init__(self, quote: FormalQuote, existing: Order | None = None) -> None:
        self.quote = quote
        self.existing = existing
        self.added: list[object] = []

    def scalar(self, statement: object):
        query = str(statement)
        if "FROM formal_quotes" in query:
            return self.quote
        if "FROM orders" in query:
            return self.existing
        raise AssertionError(query)

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        for value in self.added:
            if getattr(value, "id", None) is None and hasattr(value, "id"):
                value.id = uuid.uuid4()


def address(name: str) -> dict[str, object]:
    return {
        "recipient_name": name,
        "line1": "123 Ocean Ave",
        "line2": None,
        "city": "Irvine",
        "region_code": "CA",
        "postal_code": "92618",
        "country_code": "US",
        "phone": "+19495551234",
    }


def make_quote(
    status: FormalQuoteStatus = FormalQuoteStatus.approved,
) -> tuple[FormalQuote, uuid.UUID]:
    customer_id = uuid.uuid4()
    quote = FormalQuote(
        id=uuid.uuid4(),
        quote_request_id=uuid.uuid4(),
        revision_number=2,
        status=status,
        customer_user_id=customer_id,
        approved_by_user_id=customer_id,
        currency="USD",
        subtotal_amount_minor=250000,
        charges_amount_minor=15000,
        total_amount_minor=265000,
        delivery_address_snapshot=address("Dory Tang"),
        billing_address_snapshot=address("Dory Tang"),
    )
    quote.items = [
        FormalQuoteItem(
            id=uuid.uuid4(),
            formal_quote_id=quote.id,
            sku_snapshot="DD-ORIGIN",
            name_snapshot="Origin",
            quantity=1,
            unit_amount_minor=250000,
            line_total_minor=250000,
            currency="USD",
            pricing_policy_mode_snapshot="PRIVATE_QUOTE",
            estimated_lead_time_snapshot="2–3 weeks",
            sort_order=0,
        )
    ]
    quote.charges = [
        FormalQuoteCharge(
            id=uuid.uuid4(),
            formal_quote_id=quote.id,
            kind="shipping",
            label="Freight",
            amount_minor=25000,
            sort_order=0,
        ),
        FormalQuoteCharge(
            id=uuid.uuid4(),
            formal_quote_id=quote.id,
            kind="discount",
            label="Referral discount",
            amount_minor=-10000,
            sort_order=1,
        ),
    ]
    return quote, customer_id


def test_approved_quote_becomes_awaiting_payment_order() -> None:
    quote, customer_id = make_quote()
    db = QuoteOrderDatabase(quote)
    user = SimpleNamespace(id=customer_id)

    order = create_order_from_approved_quote(
        db,  # type: ignore[arg-type]
        formal_quote_id=quote.id,
        customer_user=user,  # type: ignore[arg-type]
    )

    assert order.formal_quote_id == quote.id
    assert order.user_id == customer_id
    assert order.status == OrderStatus.awaiting_payment
    assert order.subtotal_amount_minor == 250000
    assert order.charges_amount_minor == 15000
    assert order.total_amount_minor == 265000
    assert order.delivery_address_snapshot == quote.delivery_address_snapshot
    assert order.billing_address_snapshot == quote.billing_address_snapshot
    assert order.currency == "USD"

    order_items = [
        value for value in db.added if value.__class__.__name__ == "OrderItem"
    ]
    assert len(order_items) == 1
    assert order_items[0].sku_snapshot == "DD-ORIGIN"
    assert order_items[0].line_total_minor == 250000
    assert order_items[0].estimated_lead_time_snapshot == "2–3 weeks"

    order_charges = [value for value in db.added if isinstance(value, OrderCharge)]
    assert [(charge.kind, charge.amount_minor) for charge in order_charges] == [
        ("shipping", 25000),
        ("discount", -10000),
    ]


def test_quote_order_creation_is_idempotent() -> None:
    quote, customer_id = make_quote()
    existing = Order(
        id=uuid.uuid4(),
        user_id=customer_id,
        formal_quote_id=quote.id,
        status=OrderStatus.awaiting_payment,
        subtotal_amount_minor=250000,
        charges_amount_minor=15000,
        total_amount_minor=265000,
        currency="USD",
    )
    db = QuoteOrderDatabase(quote, existing)

    result = create_order_from_approved_quote(
        db,  # type: ignore[arg-type]
        formal_quote_id=quote.id,
        customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
    )

    assert result is existing
    assert db.added == []


def test_unapproved_quote_cannot_become_order() -> None:
    quote, customer_id = make_quote(FormalQuoteStatus.presented)
    db = QuoteOrderDatabase(quote)

    with pytest.raises(HTTPException) as exc:
        create_order_from_approved_quote(
            db,  # type: ignore[arg-type]
            formal_quote_id=quote.id,
            customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 409


def test_another_customer_cannot_materialize_quote() -> None:
    quote, _ = make_quote()
    db = QuoteOrderDatabase(quote)

    with pytest.raises(HTTPException) as exc:
        create_order_from_approved_quote(
            db,  # type: ignore[arg-type]
            formal_quote_id=quote.id,
            customer_user=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 404


def test_quote_with_inconsistent_commercial_total_is_rejected() -> None:
    quote, customer_id = make_quote()
    quote.total_amount_minor = 264999
    db = QuoteOrderDatabase(quote)

    with pytest.raises(HTTPException, match="final total"):
        create_order_from_approved_quote(
            db,  # type: ignore[arg-type]
            formal_quote_id=quote.id,
            customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
        )

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.commerce import Order, OrderStatus
from app.models.quote import FormalQuote, FormalQuoteItem, FormalQuoteStatus
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
    assert order.total_amount_minor == quote.subtotal_amount_minor
    assert order.currency == "USD"
    order_items = [value for value in db.added if value.__class__.__name__ == "OrderItem"]
    assert len(order_items) == 1
    assert order_items[0].sku_snapshot == "DD-ORIGIN"
    assert order_items[0].line_total_minor == 250000
    assert order_items[0].estimated_lead_time_snapshot == "2–3 weeks"


def test_quote_order_creation_is_idempotent() -> None:
    quote, customer_id = make_quote()
    existing = Order(
        id=uuid.uuid4(),
        user_id=customer_id,
        formal_quote_id=quote.id,
        status=OrderStatus.awaiting_payment,
        total_amount_minor=250000,
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

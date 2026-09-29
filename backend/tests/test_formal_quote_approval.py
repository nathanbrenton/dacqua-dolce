import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.quote import FormalQuoteStatus
from app.services.formal_quotes import approve_formal_quote


class ScalarRows:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeDatabase:
    def __init__(self, drafts: list[object] | None = None) -> None:
        self.added: list[object] = []
        self.drafts = drafts or []

    def add(self, value: object) -> None:
        self.added.append(value)

    def scalars(self, statement: object) -> ScalarRows:
        return ScalarRows(self.drafts)


def test_customer_approval_locks_presented_revision() -> None:
    customer_id = uuid.uuid4()
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        quote_request_id=uuid.uuid4(),
        revision_number=2,
        customer_user_id=customer_id,
        status=FormalQuoteStatus.presented,
        approved_at=None,
        approved_by_user_id=None,
        subtotal_amount_minor=249900,
        currency="USD",
    )
    customer = SimpleNamespace(id=customer_id)
    db = FakeDatabase()

    result = approve_formal_quote(
        db,  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
        customer_user=customer,  # type: ignore[arg-type]
    )

    assert result.status == FormalQuoteStatus.approved
    assert result.approved_at is not None
    assert result.approved_by_user_id == customer_id
    assert db.added


def test_customer_cannot_approve_another_customers_quote() -> None:
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        customer_user_id=uuid.uuid4(),
        status=FormalQuoteStatus.presented,
    )

    with pytest.raises(HTTPException) as exc:
        approve_formal_quote(
            FakeDatabase(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
            customer_user=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 404


def test_superseded_quote_cannot_be_approved() -> None:
    customer_id = uuid.uuid4()
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        customer_user_id=customer_id,
        status=FormalQuoteStatus.superseded,
    )

    with pytest.raises(HTTPException) as exc:
        approve_formal_quote(
            FakeDatabase(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
            customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 409

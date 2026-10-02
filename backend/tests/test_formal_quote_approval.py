import uuid
from datetime import UTC, datetime, timedelta
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


def test_customer_approval_locks_presented_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.audit.get_settings",
        lambda: SimpleNamespace(environment="test"),
    )
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
        charges_amount_minor=0,
        total_amount_minor=249900,
        currency="USD",
    )
    policy_snapshot = SimpleNamespace(
        id=uuid.uuid4(),
        kind=SimpleNamespace(value="terms"),
        version_snapshot="2026-10-01",
        content_sha256="a" * 64,
    )
    quote.policy_snapshots = [policy_snapshot]
    customer = SimpleNamespace(id=customer_id)
    db = FakeDatabase()

    result = approve_formal_quote(
        db,  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
        customer_user=customer,  # type: ignore[arg-type]
        acknowledged_policy_snapshot_ids={policy_snapshot.id},
    )

    assert result.status == FormalQuoteStatus.approved
    assert result.approved_at is not None
    assert result.approved_by_user_id == customer_id
    assert db.added


def test_expired_presented_quote_cannot_be_approved() -> None:
    customer_id = uuid.uuid4()
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        customer_user_id=customer_id,
        status=FormalQuoteStatus.presented,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    with pytest.raises(HTTPException) as exc:
        approve_formal_quote(
            FakeDatabase(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
            customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
            acknowledged_policy_snapshot_ids=set(),
        )

    assert exc.value.status_code == 409
    assert "expired" in str(exc.value.detail).lower()


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
            acknowledged_policy_snapshot_ids=set(),
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
            acknowledged_policy_snapshot_ids=set(),
        )

    assert exc.value.status_code == 409


def test_customer_policy_acknowledgment_must_match_attached_snapshots() -> None:
    customer_id = uuid.uuid4()
    policy_snapshot = SimpleNamespace(
        id=uuid.uuid4(),
        kind=SimpleNamespace(value="terms"),
        version_snapshot="2026-10-01",
        content_sha256="b" * 64,
    )
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        quote_request_id=uuid.uuid4(),
        revision_number=1,
        customer_user_id=customer_id,
        status=FormalQuoteStatus.presented,
        policy_snapshots=[policy_snapshot],
    )

    with pytest.raises(HTTPException) as exc:
        approve_formal_quote(
            FakeDatabase(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
            customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
            acknowledged_policy_snapshot_ids={uuid.uuid4()},
        )

    assert exc.value.status_code == 409

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.quote import FormalQuoteStatus, ShippingInsuranceDecision
from app.services.formal_quotes import (
    approve_formal_quote,
    record_shipping_insurance_decision,
)


class ScalarRows:
    def __init__(self, rows: list[object] | None = None) -> None:
        self.rows = rows or []

    def __iter__(self):
        return iter(self.rows)


class FakeDatabase:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)

    def scalars(self, statement: object) -> ScalarRows:
        return ScalarRows()


def insurance_charge(amount_minor: int = 2500) -> SimpleNamespace:
    return SimpleNamespace(
        kind="shipping_insurance",
        amount_minor=amount_minor,
    )


def test_customer_can_record_shipping_insurance_acceptance(
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
        revision_number=3,
        customer_user_id=customer_id,
        status=FormalQuoteStatus.presented,
        expires_at=None,
        currency="USD",
        charges=[insurance_charge()],
        shipping_insurance_decision=None,
        shipping_insurance_decided_at=None,
        shipping_insurance_decided_by_user_id=None,
    )
    db = FakeDatabase()

    result = record_shipping_insurance_decision(
        db,  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
        customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
        decision=ShippingInsuranceDecision.accepted,
    )

    assert result.shipping_insurance_decision == "accepted"
    assert result.shipping_insurance_decided_at is not None
    assert result.shipping_insurance_decided_by_user_id == customer_id
    assert db.added


def test_declined_shipping_insurance_blocks_quote_approval() -> None:
    customer_id = uuid.uuid4()
    policy_snapshot = SimpleNamespace(
        id=uuid.uuid4(),
        kind=SimpleNamespace(value="terms"),
        version_snapshot="2026-10-01",
        content_sha256="a" * 64,
    )
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        quote_request_id=uuid.uuid4(),
        revision_number=4,
        customer_user_id=customer_id,
        status=FormalQuoteStatus.presented,
        expires_at=None,
        policy_snapshots=[policy_snapshot],
        charges=[insurance_charge()],
        shipping_insurance_decision="declined",
        shipping_insurance_decided_at=datetime.now(UTC),
        shipping_insurance_decided_by_user_id=customer_id,
    )

    with pytest.raises(HTTPException) as exc:
        approve_formal_quote(
            FakeDatabase(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
            customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
            acknowledged_policy_snapshot_ids={policy_snapshot.id},
        )

    assert exc.value.status_code == 409
    assert "revised quote" in str(exc.value.detail).lower()


def test_shipping_insurance_acceptance_allows_quote_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.audit.get_settings",
        lambda: SimpleNamespace(environment="test"),
    )
    customer_id = uuid.uuid4()
    policy_snapshot = SimpleNamespace(
        id=uuid.uuid4(),
        kind=SimpleNamespace(value="terms"),
        version_snapshot="2026-10-01",
        content_sha256="a" * 64,
        structured_terms_sha256=None,
    )
    decided_at = datetime.now(UTC)
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        quote_request_id=uuid.uuid4(),
        revision_number=5,
        customer_user_id=customer_id,
        status=FormalQuoteStatus.presented,
        expires_at=None,
        policy_snapshots=[policy_snapshot],
        charges=[insurance_charge()],
        shipping_insurance_decision="accepted",
        shipping_insurance_decided_at=decided_at,
        shipping_insurance_decided_by_user_id=customer_id,
        subtotal_amount_minor=249900,
        charges_amount_minor=2500,
        total_amount_minor=252400,
        currency="USD",
        approved_at=None,
        approved_by_user_id=None,
    )

    result = approve_formal_quote(
        FakeDatabase(),  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
        customer_user=SimpleNamespace(id=customer_id),  # type: ignore[arg-type]
        acknowledged_policy_snapshot_ids={policy_snapshot.id},
    )

    assert result.status == FormalQuoteStatus.approved
    assert result.shipping_insurance_decision == "accepted"
    assert result.shipping_insurance_decided_at == decided_at
    assert result.shipping_insurance_decided_by_user_id == customer_id

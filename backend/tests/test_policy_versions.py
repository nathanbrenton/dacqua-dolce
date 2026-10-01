import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.policy import PolicyDocumentStatus, PolicyKind
from app.models.quote import CommercialChargeKind
from app.schemas.policies import PolicyDocumentCreate, RefundPolicyTerms
from app.services import policies as policy_service


class FakeDatabase:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        return None


def policy(kind: PolicyKind) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        kind=kind,
        version="2026-10-01",
        title=policy_service.POLICY_LABELS[kind],
        body=f"Approved {kind.value} text.",
        effective_at=datetime(2026, 10, 1, tzinfo=UTC),
    )


def test_quote_policy_snapshot_requires_complete_approved_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    available = {
        kind: policy(kind)
        for kind in policy_service.BASE_REQUIRED_QUOTE_POLICIES
    }

    def current(_db, *, kind):
        return available.get(kind)

    monkeypatch.setattr(policy_service, "current_approved_policy", current)

    quote = SimpleNamespace(
        id=uuid.uuid4(),
        charges=[],
        policy_snapshots=[],
    )
    db = FakeDatabase()

    snapshots = policy_service.snapshot_quote_policies(
        db,  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
    )

    assert [snapshot.kind for snapshot in snapshots] == list(
        policy_service.BASE_REQUIRED_QUOTE_POLICIES
    )
    assert all(len(snapshot.content_sha256) == 64 for snapshot in snapshots)
    assert len(db.added) == len(policy_service.BASE_REQUIRED_QUOTE_POLICIES)


def test_installation_charge_requires_installation_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    available = {
        kind: policy(kind)
        for kind in policy_service.BASE_REQUIRED_QUOTE_POLICIES
    }

    def current(_db, *, kind):
        return available.get(kind)

    monkeypatch.setattr(policy_service, "current_approved_policy", current)

    quote = SimpleNamespace(
        id=uuid.uuid4(),
        charges=[
            SimpleNamespace(
                kind=CommercialChargeKind.installation.value,
            )
        ],
        policy_snapshots=[],
    )

    with pytest.raises(HTTPException) as exc:
        policy_service.snapshot_quote_policies(
            FakeDatabase(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 409
    assert "Installation Terms" in exc.value.detail


def test_policy_status_values_are_explicit() -> None:
    assert [status.value for status in PolicyDocumentStatus] == [
        "draft",
        "approved",
        "retired",
    ]


def test_refund_policy_terms_validate_fixed_and_case_by_case_modes() -> None:
    fixed = RefundPolicyTerms(
        eligibility_mode="fixed_window_with_exception",
        return_window_days=60,
        restocking_mode="fixed_percentage",
        restocking_fee_basis_points=2500,
    )
    assert fixed.return_window_days == 60
    assert fixed.restocking_fee_basis_points == 2500
    assert fixed.merchandise_condition == "new_uninstalled"
    assert fixed.customer_pays_return_shipping_by_default is True
    assert fixed.acknowledgement_required is True

    case_by_case = RefundPolicyTerms(
        eligibility_mode="case_by_case",
        restocking_mode="case_by_case",
    )
    assert case_by_case.return_window_days is None
    assert case_by_case.restocking_fee_basis_points is None


def test_refund_policy_terms_reject_inconsistent_modes() -> None:
    with pytest.raises(ValueError):
        RefundPolicyTerms(
            eligibility_mode="case_by_case",
            return_window_days=60,
            restocking_mode="case_by_case",
        )

    with pytest.raises(ValueError):
        RefundPolicyTerms(
            eligibility_mode="fixed_window",
            restocking_mode="case_by_case",
        )

    with pytest.raises(ValueError):
        RefundPolicyTerms(
            eligibility_mode="case_by_case",
            restocking_mode="fixed_percentage",
        )


def test_only_refund_policy_accepts_structured_refund_terms() -> None:
    terms = RefundPolicyTerms(
        eligibility_mode="case_by_case",
        restocking_mode="case_by_case",
    )

    refund = PolicyDocumentCreate(
        kind=PolicyKind.refund,
        version="2026-10-01-draft",
        title="Refund Policy",
        body="Draft refund policy text.",
        refund_terms=terms,
    )
    assert refund.refund_terms == terms

    with pytest.raises(ValueError):
        PolicyDocumentCreate(
            kind=PolicyKind.shipping,
            version="2026-10-01-draft",
            title="Shipping Policy",
            body="Draft shipping policy text.",
            refund_terms=terms,
        )


def test_refund_policy_snapshot_preserves_structured_terms_and_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    available = {
        kind: policy(kind)
        for kind in policy_service.BASE_REQUIRED_QUOTE_POLICIES
    }
    refund = available[PolicyKind.refund]
    refund.structured_terms = {
        "eligibility_mode": "fixed_window_with_exception",
        "return_window_days": 60,
        "restocking_mode": "fixed_percentage",
        "restocking_fee_basis_points": 2500,
        "merchandise_condition": "new_uninstalled",
        "customer_pays_return_shipping_by_default": True,
        "outbound_shipping_refund_rule": (
            "nonrefundable_with_error_defect_or_discretion_exception"
        ),
        "acknowledgement_required": True,
    }

    def current(_db, *, kind):
        return available.get(kind)

    monkeypatch.setattr(policy_service, "current_approved_policy", current)

    quote = SimpleNamespace(
        id=uuid.uuid4(),
        charges=[],
        policy_snapshots=[],
    )
    snapshots = policy_service.snapshot_quote_policies(
        FakeDatabase(),  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
    )
    refund_snapshot = next(
        snapshot for snapshot in snapshots
        if snapshot.kind == PolicyKind.refund
    )

    assert refund_snapshot.structured_terms_snapshot == refund.structured_terms
    assert refund_snapshot.structured_terms_sha256 is not None
    assert len(refund_snapshot.structured_terms_sha256) == 64

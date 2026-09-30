import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.policy import PolicyDocumentStatus, PolicyKind
from app.models.quote import CommercialChargeKind
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

import uuid
from types import SimpleNamespace

import pytest

from app.models.audit import AuditEvent
from app.models.commerce import Order, OrderStatus
from app.services.return_policy_exceptions import (
    ReturnPolicyExceptionError,
    authorize_return_policy_exception,
)


class ExceptionDatabase:
    def __init__(self, snapshot) -> None:
        self.snapshot = snapshot
        self.added: list[object] = []

    def scalar(self, statement: object):
        query = str(statement)
        if "FROM formal_quote_policy_snapshots" in query:
            return self.snapshot
        raise AssertionError(query)

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        return None


def order() -> Order:
    return Order(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        formal_quote_id=uuid.uuid4(),
        status=OrderStatus.paid,
        subtotal_amount_minor=10000,
        charges_amount_minor=0,
        total_amount_minor=10000,
        currency="USD",
    )


def snapshot() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        version_snapshot="refund-v1",
    )


def test_return_policy_exception_records_governing_policy_and_overrides() -> None:
    db = ExceptionDatabase(snapshot())
    actor = uuid.uuid4()
    target = order()

    event = authorize_return_policy_exception(
        db,  # type: ignore[arg-type]
        order=target,
        actor_user_id=actor,
        reason="Approved customer-service exception.",
        return_window_days_override=90,
        restocking_fee_basis_points_override=0,
    )

    assert isinstance(event, AuditEvent)
    assert event.action == "order.return_policy_exception_authorized"
    assert event.entity_type == "order"
    assert event.entity_id == str(target.id)
    assert event.actor_user_id == actor
    assert event.metadata_json["refund_policy_version"] == "refund-v1"
    assert event.metadata_json["return_window_days_override"] == 90
    assert event.metadata_json["restocking_fee_basis_points_override"] == 0


def test_return_policy_exception_requires_an_override() -> None:
    with pytest.raises(ReturnPolicyExceptionError, match="At least one"):
        authorize_return_policy_exception(
            ExceptionDatabase(snapshot()),  # type: ignore[arg-type]
            order=order(),
            actor_user_id=uuid.uuid4(),
            reason="No actual override supplied.",
        )


def test_return_policy_exception_requires_snapshotted_refund_policy() -> None:
    with pytest.raises(ReturnPolicyExceptionError, match="snapshotted Refund Policy"):
        authorize_return_policy_exception(
            ExceptionDatabase(None),  # type: ignore[arg-type]
            order=order(),
            actor_user_id=uuid.uuid4(),
            reason="Exception requested.",
            restocking_fee_basis_points_override=0,
        )

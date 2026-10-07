from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.email_config import EmailRuntimeSettings
from app.models.commerce import FulfillmentStatus, OrderStatus
from app.models.email import EmailDeliveryStatus
from app.services import order_confirmations


class ConfirmationDatabase:
    def __init__(self, scalar_values: list[object | None]) -> None:
        self.scalar_values = list(scalar_values)
        self.flush_count = 0

    def scalar(self, statement: object) -> object | None:
        _ = statement
        if not self.scalar_values:
            return None
        return self.scalar_values.pop(0)

    def flush(self) -> None:
        self.flush_count += 1


def settings() -> EmailRuntimeSettings:
    return EmailRuntimeSettings(
        environment="test",
        public_origin="http://127.0.0.1:15173",
        email_provider="disabled",
        email_from="orders@example.test",
    )


def order(
    *,
    fulfillment_status: FulfillmentStatus,
    reviewed: bool = True,
    on_hold: bool = False,
) -> SimpleNamespace:
    reviewed_at = datetime.now(UTC) if reviewed else None
    return SimpleNamespace(
        id=uuid.uuid4(),
        status=OrderStatus.paid,
        fulfillment_status=fulfillment_status,
        supplier_ordered_at=(
            datetime.now(UTC)
            if fulfillment_status != FulfillmentStatus.not_started
            else None
        ),
        reviewed_at=reviewed_at,
        reviewed_by_user_id=uuid.uuid4() if reviewed else None,
        review_on_hold=on_hold,
    )


def customer() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="customer@example.test",
    )


def test_order_confirmation_requires_supplier_confirmation() -> None:
    database = ConfirmationDatabase([])

    with pytest.raises(
        order_confirmations.OrderConfirmationError,
        match="only after Supplier Confirmed",
    ):
        order_confirmations.send_order_confirmation(
            database,  # type: ignore[arg-type]
            order=order(fulfillment_status=FulfillmentStatus.not_started),  # type: ignore[arg-type]
            customer=customer(),  # type: ignore[arg-type]
            settings=settings(),
            actor_user_id=uuid.uuid4(),
        )


def test_order_confirmation_requires_formal_order_review() -> None:
    database = ConfirmationDatabase([])

    with pytest.raises(
        order_confirmations.OrderConfirmationError,
        match="only after Order Reviewed",
    ):
        order_confirmations.send_order_confirmation(
            database,  # type: ignore[arg-type]
            order=order(
                fulfillment_status=FulfillmentStatus.supplier_ordered,
                reviewed=False,
            ),  # type: ignore[arg-type]
            customer=customer(),  # type: ignore[arg-type]
            settings=settings(),
            actor_user_id=uuid.uuid4(),
        )


def test_order_confirmation_is_blocked_while_review_hold_is_active() -> None:
    database = ConfirmationDatabase([])

    with pytest.raises(
        order_confirmations.OrderConfirmationError,
        match="on hold pending customer response",
    ):
        order_confirmations.send_order_confirmation(
            database,  # type: ignore[arg-type]
            order=order(
                fulfillment_status=FulfillmentStatus.supplier_ordered,
                reviewed=True,
                on_hold=True,
            ),  # type: ignore[arg-type]
            customer=customer(),  # type: ignore[arg-type]
            settings=settings(),
            actor_user_id=uuid.uuid4(),
        )


def test_successful_order_confirmation_is_staff_controlled_and_audited(
    monkeypatch: Any,
) -> None:
    database = ConfirmationDatabase([None])
    captured: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    delivery_id = uuid.uuid4()

    def fake_delivery(
        db: object,
        **kwargs: object,
    ) -> object:
        _ = db
        captured.append(kwargs)
        return SimpleNamespace(
            id=delivery_id,
            status=EmailDeliveryStatus.sent,
        )

    monkeypatch.setattr(
        order_confirmations,
        "deliver_email",
        fake_delivery,
    )
    monkeypatch.setattr(
        order_confirmations,
        "record_audit_event",
        lambda *args, **kwargs: audits.append(kwargs),
    )

    target_order = order(
        fulfillment_status=FulfillmentStatus.supplier_ordered
    )
    target_customer = customer()
    actor_id = uuid.uuid4()

    result = order_confirmations.send_order_confirmation(
        database,  # type: ignore[arg-type]
        order=target_order,  # type: ignore[arg-type]
        customer=target_customer,  # type: ignore[arg-type]
        settings=settings(),
        actor_user_id=actor_id,
    )

    assert result.id == delivery_id
    assert database.flush_count == 1
    assert len(captured) == 1
    message = captured[0]["message"]
    assert message.subject == "Order Confirmed"
    assert "Order Confirmed" in message.body_text
    assert str(target_order.id) in message.body_text
    assert captured[0]["category"] == "order_confirmation"
    assert captured[0]["related_entity_type"] == "order"
    assert captured[0]["related_entity_id"] == str(target_order.id)
    assert captured[0]["customer_user_id"] == target_customer.id
    assert captured[0]["author_user_id"] == actor_id
    assert audits[0]["action"] == "order.confirmation_delivery"


def test_successful_order_confirmation_cannot_be_duplicated() -> None:
    existing = SimpleNamespace(
        id=uuid.uuid4(),
        status=EmailDeliveryStatus.sent,
    )
    database = ConfirmationDatabase([existing])

    with pytest.raises(
        order_confirmations.OrderConfirmationError,
        match="already been sent successfully",
    ):
        order_confirmations.send_order_confirmation(
            database,  # type: ignore[arg-type]
            order=order(
                fulfillment_status=FulfillmentStatus.supplier_ordered
            ),  # type: ignore[arg-type]
            customer=customer(),  # type: ignore[arg-type]
            settings=settings(),
            actor_user_id=uuid.uuid4(),
        )


def test_failed_or_suppressed_attempt_does_not_block_retry(
    monkeypatch: Any,
) -> None:
    database = ConfirmationDatabase([None])
    attempts = 0

    def fake_delivery(*args: object, **kwargs: object) -> object:
        nonlocal attempts
        _ = (args, kwargs)
        attempts += 1
        return SimpleNamespace(
            id=uuid.uuid4(),
            status=EmailDeliveryStatus.failed,
        )

    monkeypatch.setattr(order_confirmations, "deliver_email", fake_delivery)
    monkeypatch.setattr(
        order_confirmations,
        "record_audit_event",
        lambda *args, **kwargs: None,
    )

    order_confirmations.send_order_confirmation(
        database,  # type: ignore[arg-type]
        order=order(
            fulfillment_status=FulfillmentStatus.supplier_ordered
        ),  # type: ignore[arg-type]
        customer=customer(),  # type: ignore[arg-type]
        settings=settings(),
        actor_user_id=uuid.uuid4(),
    )

    assert attempts == 1

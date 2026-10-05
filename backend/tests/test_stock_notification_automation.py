from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.core.email_config import EmailRuntimeSettings
from app.models.catalog import InventoryStatus, ProductLifecycleStatus
from app.models.email import EmailDeliveryStatus
from app.services import stock_notifications


class ScalarRows:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class NotificationDatabase:
    def __init__(self, subscriptions: list[object]) -> None:
        self.subscriptions = subscriptions
        self.flush_count = 0

    def scalars(self, statement: object) -> ScalarRows:
        _ = statement
        return ScalarRows(self.subscriptions)

    def flush(self) -> None:
        self.flush_count += 1


def test_staff_confirmed_availability_requires_sellable_stock() -> None:
    assert stock_notifications.inventory_is_staff_confirmed_available(
        status=InventoryStatus.in_stock,
        quantity_on_hand=2,
        quantity_reserved=1,
        lifecycle_status=ProductLifecycleStatus.active,
    )
    assert stock_notifications.inventory_is_staff_confirmed_available(
        status=InventoryStatus.low_stock,
        quantity_on_hand=1,
        quantity_reserved=0,
        lifecycle_status=ProductLifecycleStatus.soon_discontinued,
    )
    assert not stock_notifications.inventory_is_staff_confirmed_available(
        status=InventoryStatus.in_stock,
        quantity_on_hand=1,
        quantity_reserved=1,
        lifecycle_status=ProductLifecycleStatus.active,
    )
    assert not stock_notifications.inventory_is_staff_confirmed_available(
        status=InventoryStatus.backordered,
        quantity_on_hand=4,
        quantity_reserved=0,
        lifecycle_status=ProductLifecycleStatus.active,
    )
    assert not stock_notifications.inventory_is_staff_confirmed_available(
        status=InventoryStatus.in_stock,
        quantity_on_hand=4,
        quantity_reserved=0,
        lifecycle_status=ProductLifecycleStatus.discontinued,
    )


def test_successful_delivery_completes_one_time_subscription(
    monkeypatch: Any,
) -> None:
    now = datetime.now(UTC)
    subscription = SimpleNamespace(
        id=uuid.uuid4(),
        email="customer@example.test",
        active=True,
        notified_at=None,
        created_at=now,
    )
    product = SimpleNamespace(
        id=uuid.uuid4(),
        name="Refine",
        sku="DD-REFINE",
        public_path="/systems/refine",
    )
    database = NotificationDatabase([subscription])
    sent_messages: list[object] = []
    audits: list[dict[str, object]] = []

    def fake_delivery(
        db: object,
        *,
        settings: object,
        message: object,
        category: str,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        **kwargs: object,
    ) -> object:
        _ = (db, settings, related_entity_type, related_entity_id, kwargs)
        sent_messages.append((message, category))
        return SimpleNamespace(
            id=uuid.uuid4(),
            status=EmailDeliveryStatus.sent,
        )

    monkeypatch.setattr(
        stock_notifications,
        "deliver_email",
        fake_delivery,
    )
    monkeypatch.setattr(
        stock_notifications,
        "record_audit_event",
        lambda *args, **kwargs: audits.append(kwargs),
    )

    result = stock_notifications.dispatch_back_in_stock_notifications(
        database,  # type: ignore[arg-type]
        product=product,  # type: ignore[arg-type]
        settings=EmailRuntimeSettings(
            environment="test",
            public_origin="http://127.0.0.1:15173",
        ),
        actor_user_id=uuid.uuid4(),
    )

    assert result.attempted == 1
    assert result.sent == 1
    assert result.failed == 0
    assert result.suppressed == 0
    assert subscription.active is False
    assert subscription.notified_at is not None
    assert sent_messages[0][1] == "stock_notification"
    message = sent_messages[0][0]
    assert "available again" in message.subject
    assert "/systems/refine" in message.body_text
    assert database.flush_count == 1
    assert audits[0]["action"] == "catalog.stock_notification_delivery"


def test_failed_delivery_stays_active_for_later_staff_retry(
    monkeypatch: Any,
) -> None:
    subscription = SimpleNamespace(
        id=uuid.uuid4(),
        email="customer@example.test",
        active=True,
        notified_at=None,
        created_at=datetime.now(UTC),
    )
    product = SimpleNamespace(
        id=uuid.uuid4(),
        name="Refine",
        sku="DD-REFINE",
        public_path="/systems/refine",
    )
    database = NotificationDatabase([subscription])

    monkeypatch.setattr(
        stock_notifications,
        "deliver_email",
        lambda *args, **kwargs: SimpleNamespace(
            id=uuid.uuid4(),
            status=EmailDeliveryStatus.failed,
        ),
    )
    monkeypatch.setattr(
        stock_notifications,
        "record_audit_event",
        lambda *args, **kwargs: None,
    )

    result = stock_notifications.dispatch_back_in_stock_notifications(
        database,  # type: ignore[arg-type]
        product=product,  # type: ignore[arg-type]
        settings=EmailRuntimeSettings(
            environment="test",
            public_origin="http://127.0.0.1:15173",
        ),
        actor_user_id=uuid.uuid4(),
    )

    assert result.attempted == 1
    assert result.sent == 0
    assert result.failed == 1
    assert subscription.active is True
    assert subscription.notified_at is None

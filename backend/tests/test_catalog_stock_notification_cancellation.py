from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

from app.api import catalog
from app.schemas.catalog import StockNotificationRequest


class CancellationDatabase:
    def __init__(
        self,
        *,
        product: object,
        subscription: object | None,
    ) -> None:
        self.product = product
        self.subscription = subscription
        self.scalar_calls = 0
        self.committed = False

    def __enter__(self) -> CancellationDatabase:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def scalar(self, statement: object) -> object | None:
        _ = statement
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return self.product
        return self.subscription

    def commit(self) -> None:
        self.committed = True


def test_customer_can_cancel_active_availability_notice(
    monkeypatch: Any,
) -> None:
    product = SimpleNamespace(
        id=uuid.uuid4(),
        slug="refine",
        sku="DD-REFINE",
    )
    subscription = SimpleNamespace(
        id=uuid.uuid4(),
        active=True,
    )
    database = CancellationDatabase(
        product=product,
        subscription=subscription,
    )
    audits: list[dict[str, object]] = []

    monkeypatch.setattr(
        catalog,
        "SessionLocal",
        lambda: database,
    )
    monkeypatch.setattr(
        catalog,
        "record_audit_event",
        lambda *args, **kwargs: audits.append(kwargs),
    )

    response = catalog.cancel_stock_notification(
        "refine",
        StockNotificationRequest(
            email="Customer@Example.Test",
        ),
    )

    assert response.status == "cancelled"
    assert "has been cancelled" in response.message
    assert subscription.active is False
    assert database.committed is True
    assert audits[0]["action"] == "catalog.stock_notification_cancelled"


def test_cancel_response_does_not_reveal_missing_subscription(
    monkeypatch: Any,
) -> None:
    product = SimpleNamespace(
        id=uuid.uuid4(),
        slug="refine",
        sku="DD-REFINE",
    )
    database = CancellationDatabase(
        product=product,
        subscription=None,
    )
    audits: list[dict[str, object]] = []

    monkeypatch.setattr(
        catalog,
        "SessionLocal",
        lambda: database,
    )
    monkeypatch.setattr(
        catalog,
        "record_audit_event",
        lambda *args, **kwargs: audits.append(kwargs),
    )

    response = catalog.cancel_stock_notification(
        "refine",
        StockNotificationRequest(
            email="missing@example.test",
        ),
    )

    assert response.status == "cancelled"
    assert "If an active availability notice existed" in response.message
    assert database.committed is True
    assert audits == []

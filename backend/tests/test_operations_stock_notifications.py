from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.api import operations


class Rows:
    def __init__(self, values: list[tuple[object, object]]) -> None:
        self.values = values

    def all(self) -> list[tuple[object, object]]:
        return self.values


class NotificationDatabase:
    def __init__(self, rows: list[tuple[object, object]]) -> None:
        self.rows = rows
        self.statement: object | None = None

    def execute(self, statement: object) -> Rows:
        self.statement = statement
        return Rows(self.rows)


def test_stock_notification_list_returns_customer_demand(
    monkeypatch: Any,
) -> None:
    now = datetime.now(UTC)
    product_id = uuid.uuid4()
    subscription = SimpleNamespace(
        id=uuid.uuid4(),
        product_id=product_id,
        email="customer@example.test",
        active=True,
        notified_at=None,
        created_at=now,
        updated_at=now,
    )
    product = SimpleNamespace(
        id=product_id,
        sku="DD-TEST",
        name="Test System",
    )
    db = NotificationDatabase([(subscription, product)])
    actor = object()
    seen: list[object] = []

    monkeypatch.setattr(
        operations,
        "require_operations",
        lambda db, *, user: seen.append(user),
    )

    result = operations.list_stock_notifications(
        db,  # type: ignore[arg-type]
        actor,  # type: ignore[arg-type]
    )

    assert seen == [actor]
    assert len(result) == 1
    assert result[0].product_id == str(product_id)
    assert result[0].product_sku == "DD-TEST"
    assert result[0].product_name == "Test System"
    assert result[0].email == "customer@example.test"
    assert result[0].active is True
    assert result[0].notified_at is None
    assert result[0].created_at == now.isoformat()

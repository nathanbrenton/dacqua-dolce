import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.models.catalog import (
    InventoryStatus,
)
from app.services import commerce


class ScalarDatabase:
    def __init__(
        self,
        result: int,
    ) -> None:
        self.result = result
        self.statement: object | None = None

    def scalar(
        self,
        statement: object,
    ) -> int:
        self.statement = statement
        return self.result


def test_active_reserved_quantity_counts_only_live_holds() -> None:
    database = ScalarDatabase(3)
    product_id = uuid.uuid4()

    result = commerce.active_reserved_quantity(
        database,  # type: ignore[arg-type]
        product_id=product_id,
        variant_id=None,
        now=datetime.now(UTC),
    )

    assert result == 3

    query = str(database.statement)

    assert "cart_items.quantity" in query
    assert "cart_items.reservation_expires_at" in query
    assert "carts.status" in query
    assert "cart_items.product_id" in query


def test_existing_live_hold_can_be_extended_within_capacity(
    monkeypatch: Any,
) -> None:
    now = datetime.now(UTC)
    product_id = uuid.uuid4()

    inventory = SimpleNamespace(
        product_id=product_id,
        variant_id=None,
        inventory_status=(
            InventoryStatus.in_stock
        ),
        quantity_on_hand=4,
    )

    item = SimpleNamespace(
        quantity=2,
        reservation_expires_at=(
            now + commerce.CART_RESERVATION_TTL
        ),
    )

    monkeypatch.setattr(
        commerce,
        "active_reserved_quantity",
        lambda *args, **kwargs: 2,
    )

    commerce._reserve_quantity(
        object(),  # type: ignore[arg-type]
        item=item,  # type: ignore[arg-type]
        inventory=inventory,  # type: ignore[arg-type]
        desired_quantity=3,
        now=now,
    )

    assert item.reservation_expires_at == (
        now + commerce.CART_RESERVATION_TTL
    )


def test_reservation_rejects_oversubscription(
    monkeypatch: Any,
) -> None:
    now = datetime.now(UTC)

    inventory = SimpleNamespace(
        product_id=uuid.uuid4(),
        variant_id=None,
        inventory_status=(
            InventoryStatus.in_stock
        ),
        quantity_on_hand=4,
    )

    item = SimpleNamespace(
        quantity=2,
        reservation_expires_at=(
            now + commerce.CART_RESERVATION_TTL
        ),
    )

    monkeypatch.setattr(
        commerce,
        "active_reserved_quantity",
        lambda *args, **kwargs: 4,
    )

    with pytest.raises(
        commerce.CommerceError,
        match="not currently available",
    ):
        commerce._reserve_quantity(
            object(),  # type: ignore[arg-type]
            item=item,  # type: ignore[arg-type]
            inventory=inventory,  # type: ignore[arg-type]
            desired_quantity=3,
            now=now,
        )


def test_not_tracked_inventory_does_not_hold_stock() -> None:
    now = datetime.now(UTC)

    inventory = SimpleNamespace(
        product_id=uuid.uuid4(),
        variant_id=None,
        inventory_status=(
            InventoryStatus.not_tracked
        ),
        quantity_on_hand=0,
    )

    item = SimpleNamespace(
        quantity=1,
        reservation_expires_at=(
            now + commerce.CART_RESERVATION_TTL
        ),
    )

    commerce._reserve_quantity(
        object(),  # type: ignore[arg-type]
        item=item,  # type: ignore[arg-type]
        inventory=inventory,  # type: ignore[arg-type]
        desired_quantity=1,
        now=now,
    )

    assert item.reservation_expires_at is None

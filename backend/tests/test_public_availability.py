"""Tests for customer-safe inventory presentation."""

from types import SimpleNamespace

from app.models.catalog import InventoryStatus
from app.services.public_availability import (
    resolve_public_availability,
)


def inventory(
    status: InventoryStatus,
    quantity: int,
):
    return SimpleNamespace(
        inventory_status=status,
        quantity_on_hand=quantity,
    )


def test_untracked_inventory_requires_confirmation() -> None:
    result = resolve_public_availability(
        inventory(
            InventoryStatus.not_tracked,
            0,
        )
    )

    assert result.status == "contact"
    assert result.available is None


def test_unapproved_online_sale_hides_inventory_state() -> None:
    result = resolve_public_availability(
        inventory(
            InventoryStatus.in_stock,
            10,
        ),
        online_sale_approved=False,
    )

    assert result.status == "contact"
    assert result.available is None


def test_in_stock_inventory_is_available() -> None:
    result = resolve_public_availability(
        inventory(
            InventoryStatus.in_stock,
            10,
        ),
        reserved_quantity=3,
    )

    assert result.status == "in_stock"
    assert result.available is True


def test_reservations_can_exhaust_public_availability() -> None:
    result = resolve_public_availability(
        inventory(
            InventoryStatus.in_stock,
            3,
        ),
        reserved_quantity=3,
    )

    assert result.status == "unavailable"
    assert result.available is False


def test_low_stock_remains_customer_safe() -> None:
    result = resolve_public_availability(
        inventory(
            InventoryStatus.low_stock,
            2,
        ),
        reserved_quantity=1,
    )

    assert result.status == "low_stock"
    assert result.available is True


def test_backordered_inventory_is_not_available() -> None:
    result = resolve_public_availability(
        inventory(
            InventoryStatus.backordered,
            0,
        )
    )

    assert result.status == "backordered"
    assert result.available is False

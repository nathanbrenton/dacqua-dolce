"""Tests for customer-safe inventory presentation."""

from datetime import date
from types import SimpleNamespace

from app.models.catalog import InventoryStatus, ProductLifecycleStatus
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
        expected_available_on=None,
        estimated_lead_time=None,
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

    assert result.status == "out_of_stock"
    assert result.available is False
    assert result.can_notify_when_in_stock is True


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

    assert result.status == "out_of_stock"
    assert result.available is False
    assert result.can_notify_when_in_stock is True

def test_out_of_stock_remains_visible_for_quote_only_product() -> None:
    item = inventory(InventoryStatus.unavailable, 0)
    item.estimated_lead_time = "2–3 weeks"

    result = resolve_public_availability(
        item,
        online_sale_approved=False,
    )

    assert result.status == "out_of_stock"
    assert result.available is False
    assert result.estimated_lead_time == "2–3 weeks"
    assert result.action == "INQUIRE"


def test_expected_date_takes_structured_public_field() -> None:
    item = inventory(InventoryStatus.backordered, 0)
    item.expected_available_on = date(2026, 11, 15)

    result = resolve_public_availability(item)

    assert result.status == "out_of_stock"
    assert result.expected_available_on == "2026-11-15"


def test_discontinued_is_distinct_from_out_of_stock() -> None:
    result = resolve_public_availability(
        inventory(InventoryStatus.unavailable, 0),
        lifecycle_status=ProductLifecycleStatus.discontinued,
    )

    assert result.status == "discontinued"
    assert result.lifecycle_status == "discontinued"
    assert result.can_notify_when_in_stock is False
    assert result.can_inquire is True


def test_soon_discontinued_can_remain_in_stock() -> None:
    result = resolve_public_availability(
        inventory(InventoryStatus.in_stock, 3),
        lifecycle_status=ProductLifecycleStatus.soon_discontinued,
    )

    assert result.status == "in_stock"
    assert result.lifecycle_status == "soon_discontinued"
    assert result.available is True


def test_unavailable_inquiry_can_be_disabled_per_product() -> None:
    result = resolve_public_availability(
        inventory(InventoryStatus.unavailable, 0),
        allow_inquiry_when_unavailable=False,
    )

    assert result.status == "out_of_stock"
    assert result.can_inquire is False
    assert result.action == "UNAVAILABLE"

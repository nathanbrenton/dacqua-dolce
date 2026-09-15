"""Customer-safe product availability decisions."""

from dataclasses import dataclass

from app.models.catalog import (
    InventoryStatus,
    ProductInventory,
)


@dataclass(frozen=True, slots=True)
class PublicAvailabilityDecision:
    """Availability information safe for public/customer presentation."""

    status: str
    available: bool | None
    action: str
    action_label: str


def resolve_public_availability(
    inventory: ProductInventory | None,
    *,
    reserved_quantity: int = 0,
    online_sale_approved: bool = True,
) -> PublicAvailabilityDecision:
    """Resolve internal inventory into a customer-safe availability state."""

    if not online_sale_approved:
        return PublicAvailabilityDecision(
            status="contact",
            available=None,
            action="REQUEST_QUOTE",
            action_label="Contact for Availability",
        )

    if (
        inventory is None
        or inventory.inventory_status
        == InventoryStatus.not_tracked
    ):
        return PublicAvailabilityDecision(
            status="contact",
            available=None,
            action="CONTACT",
            action_label="Contact for Availability",
        )

    if inventory.inventory_status == InventoryStatus.unavailable:
        return PublicAvailabilityDecision(
            status="unavailable",
            available=False,
            action="CONTACT",
            action_label="Contact for Availability",
        )

    if inventory.inventory_status == InventoryStatus.backordered:
        return PublicAvailabilityDecision(
            status="backordered",
            available=False,
            action="CONTACT",
            action_label="Contact for Availability",
        )

    available_quantity = (
        inventory.quantity_on_hand
        - max(reserved_quantity, 0)
    )

    if available_quantity <= 0:
        return PublicAvailabilityDecision(
            status="unavailable",
            available=False,
            action="CONTACT",
            action_label="Contact for Availability",
        )

    if inventory.inventory_status == InventoryStatus.low_stock:
        return PublicAvailabilityDecision(
            status="low_stock",
            available=True,
            action="AVAILABLE",
            action_label="Limited Availability",
        )

    return PublicAvailabilityDecision(
        status="in_stock",
        available=True,
        action="AVAILABLE",
        action_label="Available",
    )

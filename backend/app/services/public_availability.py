"""Customer-safe product availability decisions."""

from dataclasses import dataclass

from app.models.catalog import (
    InventoryStatus,
    ProductInventory,
    ProductLifecycleStatus,
)


@dataclass(frozen=True, slots=True)
class PublicAvailabilityDecision:
    """Availability information safe for public/customer presentation."""

    status: str
    available: bool | None
    action: str
    action_label: str
    lifecycle_status: str = ProductLifecycleStatus.active.value
    expected_available_on: str | None = None
    estimated_lead_time: str | None = None
    can_notify_when_in_stock: bool = False
    can_inquire: bool = True


def resolve_public_availability(
    inventory: ProductInventory | None,
    *,
    reserved_quantity: int = 0,
    online_sale_approved: bool = True,
    lifecycle_status: ProductLifecycleStatus = ProductLifecycleStatus.active,
    allow_inquiry_when_unavailable: bool = True,
) -> PublicAvailabilityDecision:
    """Resolve stock and product lifecycle into customer-safe availability.

    Product lifecycle and temporary stock state stay separate. A discontinued
    product is never presented as merely out of stock. A soon-to-be-
    discontinued product can remain available while stock lasts.
    """

    lifecycle = lifecycle_status.value

    if lifecycle_status == ProductLifecycleStatus.discontinued:
        return PublicAvailabilityDecision(
            status="discontinued",
            available=False,
            action=("INQUIRE" if allow_inquiry_when_unavailable else "UNAVAILABLE"),
            action_label=("Send inquiry" if allow_inquiry_when_unavailable else "Unavailable"),
            lifecycle_status=lifecycle,
            can_notify_when_in_stock=False,
            can_inquire=allow_inquiry_when_unavailable,
        )

    if (
        inventory is None
        or inventory.inventory_status == InventoryStatus.not_tracked
    ):
        return PublicAvailabilityDecision(
            status="contact",
            available=None,
            action="CONTACT",
            action_label="Contact for Availability",
            lifecycle_status=lifecycle,
            can_inquire=True,
        )

    lead_time = inventory.estimated_lead_time
    expected_available_on = (
        inventory.expected_available_on.isoformat()
        if inventory.expected_available_on is not None
        else None
    )

    if inventory.inventory_status in {
        InventoryStatus.unavailable,
        InventoryStatus.backordered,
    }:
        return PublicAvailabilityDecision(
            status="out_of_stock",
            available=False,
            action=("INQUIRE" if allow_inquiry_when_unavailable else "UNAVAILABLE"),
            action_label=("Send inquiry" if allow_inquiry_when_unavailable else "Unavailable"),
            lifecycle_status=lifecycle,
            expected_available_on=expected_available_on,
            estimated_lead_time=lead_time,
            can_notify_when_in_stock=True,
            can_inquire=allow_inquiry_when_unavailable,
        )

    available_quantity = inventory.quantity_on_hand - max(reserved_quantity, 0)

    if available_quantity <= 0:
        return PublicAvailabilityDecision(
            status="out_of_stock",
            available=False,
            action=("INQUIRE" if allow_inquiry_when_unavailable else "UNAVAILABLE"),
            action_label=("Send inquiry" if allow_inquiry_when_unavailable else "Unavailable"),
            lifecycle_status=lifecycle,
            expected_available_on=expected_available_on,
            estimated_lead_time=lead_time,
            can_notify_when_in_stock=True,
            can_inquire=allow_inquiry_when_unavailable,
        )

    if not online_sale_approved:
        return PublicAvailabilityDecision(
            status="contact",
            available=None,
            action="REQUEST_QUOTE",
            action_label="Contact for Availability",
            lifecycle_status=lifecycle,
            can_inquire=True,
        )

    if inventory.inventory_status == InventoryStatus.low_stock:
        return PublicAvailabilityDecision(
            status="low_stock",
            available=True,
            action="AVAILABLE",
            action_label="Limited Availability",
            lifecycle_status=lifecycle,
            can_inquire=True,
        )

    return PublicAvailabilityDecision(
        status="in_stock",
        available=True,
        action="AVAILABLE",
        action_label="Available",
        lifecycle_status=lifecycle,
        can_inquire=True,
    )

from dataclasses import dataclass
from datetime import date, datetime

from app.models.catalog import (
    InventorySourceKind,
    InventoryStatus,
    ProductInventory,
)


@dataclass(frozen=True)
class InventoryObservation:
    status: InventoryStatus
    quantity_on_hand: int
    expected_available_on: date | None
    estimated_lead_time: str | None
    source_kind: InventorySourceKind
    source_reference: str | None
    observed_at: datetime


def apply_inventory_observation(
    inventory: ProductInventory,
    observation: InventoryObservation,
) -> ProductInventory:
    """Apply one normalized inventory observation to the authoritative row.

    Provider-specific adapters can normalize their future payloads into this
    structure without leaking supplier/manufacturer API details into catalog
    or customer-facing code.
    """

    inventory.inventory_status = observation.status
    inventory.quantity_on_hand = observation.quantity_on_hand
    inventory.expected_available_on = observation.expected_available_on
    inventory.estimated_lead_time = observation.estimated_lead_time
    inventory.source_kind = observation.source_kind
    inventory.source_reference = observation.source_reference
    inventory.source_observed_at = observation.observed_at
    return inventory

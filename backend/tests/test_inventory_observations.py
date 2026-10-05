from datetime import UTC, datetime

from app.models.catalog import (
    InventorySourceKind,
    InventoryStatus,
    ProductInventory,
)
from app.services.inventory_observations import (
    InventoryObservation,
    apply_inventory_observation,
)


def test_inventory_observation_updates_authoritative_fields() -> None:
    inventory = ProductInventory()
    observed_at = datetime(2026, 9, 29, 21, 15, tzinfo=UTC)

    result = apply_inventory_observation(
        inventory,
        InventoryObservation(
            status=InventoryStatus.backordered,
            quantity_on_hand=0,
            expected_available_on=None,
            estimated_lead_time="2–3 weeks",
            source_kind=InventorySourceKind.supplier_report,
            source_reference="Supplier portal",
            observed_at=observed_at,
        ),
    )

    assert result is inventory
    assert inventory.inventory_status == InventoryStatus.backordered
    assert inventory.quantity_on_hand == 0
    assert inventory.estimated_lead_time == "2–3 weeks"
    assert inventory.source_kind == InventorySourceKind.supplier_report
    assert inventory.source_reference == "Supplier portal"
    assert inventory.source_observed_at == observed_at

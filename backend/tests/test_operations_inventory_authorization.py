import uuid

import pytest
from fastapi import HTTPException

from app.api import operations as operations_api
from app.models.catalog import InventoryStatus
from app.schemas.operations import InventoryUpdateRequest


def test_inventory_update_uses_pricing_inventory_write_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = object()
    db = object()
    calls: list[object] = []

    def reject_inventory_write(_db: object, *, user: object) -> None:
        calls.append(user)
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    monkeypatch.setattr(
        operations_api,
        "require_pricing_inventory_write",
        reject_inventory_write,
    )

    with pytest.raises(HTTPException) as exc:
        operations_api.update_product_inventory(
            uuid.uuid4(),
            InventoryUpdateRequest(
                status=InventoryStatus.not_tracked,
                quantity_on_hand=0,
            ),
            db,
            actor,
        )

    assert exc.value.status_code == 403
    assert calls == [actor]

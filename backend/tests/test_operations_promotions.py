import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import operations as operations_api
from app.models.catalog import PricingPolicyMode, ProductPrice
from app.schemas.operations import PromotionCreateRequest


class FakeDb:
    def __init__(self, product: object) -> None:
        self.product = product
        self.added: list[object] = []
        self.commits = 0

    def add(self, row: object) -> None:
        self.added.append(row)
        if isinstance(row, ProductPrice):
            if row.id is None:
                row.id = uuid.uuid4()
            self.product.prices.append(row)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1


def standard_price(
    *,
    mode: PricingPolicyMode = PricingPolicyMode.PUBLIC,
    amount_minor: int = 12500,
) -> ProductPrice:
    return ProductPrice(
        id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        variant_id=None,
        pricing_policy_mode=mode,
        amount_minor=amount_minor,
        currency="USD",
        effective_from=datetime.now(UTC) - timedelta(days=10),
        effective_until=None,
        active=True,
    )


def test_schedule_promotion_inherits_standard_policy_and_currency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = standard_price()
    product = SimpleNamespace(id=base.product_id, sku="DD-TEST", prices=[base])
    db = FakeDb(product)
    actor = SimpleNamespace(id=uuid.uuid4())
    audit: list[dict[str, object]] = []
    sentinel = object()

    monkeypatch.setattr(
        operations_api,
        "require_pricing_inventory_write",
        lambda _db, *, user: None,
    )
    monkeypatch.setattr(
        operations_api,
        "load_product_for_operations",
        lambda _db, _product_id: product,
    )
    monkeypatch.setattr(
        operations_api,
        "record_audit_event",
        lambda _db, **kwargs: audit.append(kwargs),
    )
    monkeypatch.setattr(
        operations_api,
        "operations_product_read",
        lambda _db, *, product: sentinel,
    )

    start = datetime.now(UTC) + timedelta(hours=1)
    result = operations_api.schedule_product_promotion(
        product.id,
        PromotionCreateRequest(
            amount_minor=9900,
            effective_from=start,
            effective_until=start + timedelta(days=2),
        ),
        db,
        actor,
    )

    assert result is sentinel
    promotion = db.added[0]
    assert isinstance(promotion, ProductPrice)
    assert promotion.pricing_policy_mode == PricingPolicyMode.PUBLIC
    assert promotion.currency == "USD"
    assert promotion.amount_minor == 9900
    assert promotion.effective_until is not None
    assert db.commits == 1
    assert audit[0]["action"] == "catalog.promotion_scheduled"


def test_schedule_promotion_rejects_map_limited_standard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = standard_price(mode=PricingPolicyMode.MAP_LIMITED)
    product = SimpleNamespace(id=base.product_id, sku="DD-MAP", prices=[base])
    db = FakeDb(product)
    actor = SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(
        operations_api,
        "require_pricing_inventory_write",
        lambda _db, *, user: None,
    )
    monkeypatch.setattr(
        operations_api,
        "load_product_for_operations",
        lambda _db, _product_id: product,
    )

    start = datetime.now(UTC) + timedelta(hours=1)
    with pytest.raises(HTTPException, match="MAP-limited promotions") as exc:
        operations_api.schedule_product_promotion(
            product.id,
            PromotionCreateRequest(
                amount_minor=9900,
                effective_from=start,
                effective_until=start + timedelta(days=1),
            ),
            db,
            actor,
        )

    assert exc.value.status_code == 409
    assert db.added == []


def test_schedule_promotion_rejects_overlapping_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)
    base = standard_price()
    existing = ProductPrice(
        id=uuid.uuid4(),
        product_id=base.product_id,
        variant_id=None,
        pricing_policy_mode=PricingPolicyMode.PUBLIC,
        amount_minor=11000,
        currency="USD",
        effective_from=now + timedelta(hours=2),
        effective_until=now + timedelta(days=2),
        active=True,
    )
    product = SimpleNamespace(
        id=base.product_id,
        sku="DD-TEST",
        prices=[base, existing],
    )
    db = FakeDb(product)
    actor = SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(
        operations_api,
        "require_pricing_inventory_write",
        lambda _db, *, user: None,
    )
    monkeypatch.setattr(
        operations_api,
        "load_product_for_operations",
        lambda _db, _product_id: product,
    )

    with pytest.raises(HTTPException, match="overlaps") as exc:
        operations_api.schedule_product_promotion(
            product.id,
            PromotionCreateRequest(
                amount_minor=9900,
                effective_from=now + timedelta(hours=3),
                effective_until=now + timedelta(days=1),
            ),
            db,
            actor,
        )

    assert exc.value.status_code == 409
    assert db.added == []

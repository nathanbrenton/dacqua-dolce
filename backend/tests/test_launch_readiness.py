from datetime import UTC, datetime
from types import SimpleNamespace

from app.core.sales_area import SalesAreaPolicy
from app.models.catalog import (
    InventorySourceKind,
    InventoryStatus,
    ProductDocumentType,
)
from app.services import launch_readiness


def sale_ready_product(name: str = "Harmony") -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        documents=[
            SimpleNamespace(
                document_type=ProductDocumentType.warranty,
                active=True,
                public=True,
                verified_at=datetime.now(UTC),
                checksum_sha256="a" * 64,
            )
        ],
        inventory=[
            SimpleNamespace(
                source_kind=InventorySourceKind.supplier_report,
                source_observed_at=datetime.now(UTC),
                inventory_status=InventoryStatus.in_stock,
            )
        ],
    )


def test_launch_readiness_reports_dynamic_checks_ready(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        launch_readiness,
        "load_sales_area_policy",
        lambda: SalesAreaPolicy(
            mode="allowlist",
            country_code="US",
            region_codes=frozenset({"CA", "OR"}),
            label="Launch area",
        ),
    )
    monkeypatch.setattr(
        launch_readiness,
        "current_approved_policy",
        lambda _db, *, kind: SimpleNamespace(
            version=f"{kind.value}-v1",
        ),
    )
    monkeypatch.setattr(
        launch_readiness,
        "_load_commercial_products",
        lambda _db: [sale_ready_product()],
    )

    snapshot = launch_readiness.build_launch_readiness(
        object(),  # type: ignore[arg-type]
    )

    assert snapshot.status == "deferred"
    assert snapshot.ready_count == 4
    assert snapshot.action_required_count == 0
    assert snapshot.deferred_count == 3
    assert [check.key for check in snapshot.checks] == [
        "sales_area",
        "policies",
        "warranties",
        "catalog_inventory",
        "payment_checkout",
        "tax",
        "shipping_insurance",
    ]


def test_launch_readiness_surfaces_configuration_action_items(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        launch_readiness,
        "load_sales_area_policy",
        lambda: SalesAreaPolicy(
            mode="disabled",
            country_code="US",
            region_codes=frozenset(),
            label="Launch area",
        ),
    )
    monkeypatch.setattr(
        launch_readiness,
        "current_approved_policy",
        lambda _db, *, kind: (
            None
            if kind.value == "shipping"
            else SimpleNamespace(version="approved")
        ),
    )
    product = sale_ready_product("Origin")
    product.documents = []
    product.inventory = []
    monkeypatch.setattr(
        launch_readiness,
        "_load_commercial_products",
        lambda _db: [product],
    )

    snapshot = launch_readiness.build_launch_readiness(
        object(),  # type: ignore[arg-type]
    )

    assert snapshot.status == "action_required"
    assert snapshot.action_required_count == 4
    assert snapshot.deferred_count == 3
    assert snapshot.ready_count == 0

    checks = {check.key: check for check in snapshot.checks}
    assert checks["sales_area"].status == "action_required"
    assert checks["policies"].status == "action_required"
    assert "Shipping Policy" in " ".join(checks["policies"].evidence)
    assert checks["warranties"].status == "action_required"
    assert checks["catalog_inventory"].status == "action_required"


def test_launch_readiness_has_no_global_feature_toggle() -> None:
    deferred = {
        launch_readiness._payment_check().key,
        launch_readiness._tax_check().key,
        launch_readiness._shipping_insurance_check().key,
    }

    assert deferred == {
        "payment_checkout",
        "tax",
        "shipping_insurance",
    }

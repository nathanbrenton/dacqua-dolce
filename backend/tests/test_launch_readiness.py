from datetime import UTC, datetime
from types import SimpleNamespace

from app.core.sales_area import (
    APPROVED_LAUNCH_COUNTRY_CODE,
    APPROVED_LAUNCH_REGION_CODES,
    SalesAreaPolicy,
)
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
        tax_classifications=[
            SimpleNamespace(
                provider="stripe_tax",
                tax_code="txcd_reviewed_test",
                source_reference="Reviewed Stripe Tax code catalog",
                active=True,
            )
        ],
    )


def approved_policy(kind) -> SimpleNamespace:
    structured_terms = None
    if kind.value == "refund":
        structured_terms = {
            "eligibility_mode": "fixed_window_with_exception",
            "return_window_days": 60,
            "restocking_mode": "fixed_percentage",
            "restocking_fee_basis_points": 1500,
            "merchandise_condition": "new_uninstalled",
            "customer_pays_return_shipping_by_default": True,
            "outbound_shipping_refund_rule": (
                "nonrefundable_with_error_defect_or_discretion_exception"
            ),
            "acknowledgement_required": True,
        }
    return SimpleNamespace(
        kind=kind,
        version=f"{kind.value}-v1",
        structured_terms=structured_terms,
    )


def test_launch_readiness_reports_dynamic_checks_ready(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        launch_readiness,
        "load_sales_area_policy",
        lambda: SalesAreaPolicy(
            mode="allowlist",
            country_code=APPROVED_LAUNCH_COUNTRY_CODE,
            region_codes=APPROVED_LAUNCH_REGION_CODES,
            label="Launch area",
        ),
    )
    monkeypatch.setattr(
        launch_readiness,
        "current_approved_policy",
        lambda _db, *, kind: approved_policy(kind),
    )
    monkeypatch.setattr(
        launch_readiness,
        "_load_commercial_products",
        lambda _db: [sale_ready_product()],
    )

    snapshot = launch_readiness.build_launch_readiness(
        object(),  # type: ignore[arg-type]
    )

    assert snapshot.status == "action_required"
    assert snapshot.ready_count == 4
    assert snapshot.action_required_count == 2
    assert snapshot.deferred_count == 1
    assert snapshot.launch_phase == "prelaunch"
    assert snapshot.launch_phase_label == "Prelaunch"
    assert snapshot.commerce_checkout_allowed is False
    assert snapshot.commerce_blockers == (
        "Payment & checkout",
        "Automated sales tax",
    )
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
            else approved_policy(kind)
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
    assert snapshot.action_required_count == 6
    assert snapshot.deferred_count == 1
    assert snapshot.ready_count == 0

    checks = {check.key: check for check in snapshot.checks}
    assert checks["sales_area"].status == "action_required"
    assert checks["policies"].status == "action_required"
    assert "Shipping Policy" in " ".join(checks["policies"].evidence)
    assert checks["warranties"].status == "action_required"
    assert checks["catalog_inventory"].status == "action_required"


def test_public_launch_phase_stays_closed_while_readiness_blockers_remain(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        launch_readiness,
        "load_launch_runtime_settings",
        lambda: SimpleNamespace(phase="public_launch"),
    )
    checks = (
        launch_readiness.LaunchReadinessCheck(
            key="payment_checkout",
            label="Payment & checkout",
            status="action_required",
            detail="Provider not commissioned.",
        ),
        launch_readiness.LaunchReadinessCheck(
            key="sales_area",
            label="Sales area",
            status="ready",
            detail="Ready.",
        ),
    )

    phase, label, allowed, detail, blockers = (
        launch_readiness._commerce_gate_snapshot(checks)
    )

    assert phase == "public_launch"
    assert label == "Public launch"
    assert allowed is False
    assert "blockers remain" in detail
    assert blockers == ("Payment & checkout",)


def test_launch_readiness_rejects_allowlist_drift_from_approved_pt35_area(
    monkeypatch,
) -> None:
    drifted_regions = (
        APPROVED_LAUNCH_REGION_CODES - {"DC"}
    ) | {"AK"}
    monkeypatch.setattr(
        launch_readiness,
        "load_sales_area_policy",
        lambda: SalesAreaPolicy(
            mode="allowlist",
            country_code=APPROVED_LAUNCH_COUNTRY_CODE,
            region_codes=frozenset(drifted_regions),
            label="Launch area",
        ),
    )

    check = launch_readiness._sales_area_check()

    assert check.status == "action_required"
    assert "approved PT35 launch territory" in check.detail
    assert "Missing approved regions: DC" in check.evidence
    assert "Unexpected regions: AK" in check.evidence


def test_launch_readiness_rejects_wrong_launch_country(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        launch_readiness,
        "load_sales_area_policy",
        lambda: SalesAreaPolicy(
            mode="allowlist",
            country_code="CA",
            region_codes=APPROVED_LAUNCH_REGION_CODES,
            label="Launch area",
        ),
    )

    check = launch_readiness._sales_area_check()

    assert check.status == "action_required"
    assert (
        "Configured country does not match the approved launch country."
        in check.evidence
    )


def test_launch_readiness_requires_structured_refund_terms(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        launch_readiness,
        "current_approved_policy",
        lambda _db, *, kind: (
            SimpleNamespace(
                kind=kind,
                version="refund-v1",
                structured_terms=None,
            )
            if kind.value == "refund"
            else approved_policy(kind)
        ),
    )

    check = launch_readiness._policy_check(
        object(),  # type: ignore[arg-type]
    )

    assert check.status == "action_required"
    assert "structured return terms are missing or invalid" in " ".join(
        check.evidence
    )


def test_launch_readiness_accepts_future_refund_policy_values_without_code_change(
    monkeypatch,
) -> None:
    def current(_db, *, kind):
        policy = approved_policy(kind)
        if kind.value == "refund":
            policy.structured_terms = {
                **policy.structured_terms,
                "return_window_days": 30,
                "restocking_fee_basis_points": 1000,
            }
        return policy

    monkeypatch.setattr(
        launch_readiness,
        "current_approved_policy",
        current,
    )

    check = launch_readiness._policy_check(
        object(),  # type: ignore[arg-type]
    )

    assert check.status == "ready"
    assert "30-day return window" in " ".join(check.evidence)
    assert "10.00% restocking fee" in " ".join(check.evidence)


def test_launch_readiness_has_no_global_feature_toggle() -> None:
    payment = launch_readiness._payment_check()
    shipping = launch_readiness._shipping_insurance_check()
    tax = launch_readiness._tax_check([sale_ready_product()])

    assert payment.key == "payment_checkout"
    assert payment.status == "action_required"
    assert "Authorize.Net" in " ".join(payment.evidence)
    assert shipping.key == "shipping_insurance"
    assert shipping.status == "deferred"
    assert tax.key == "tax"
    assert tax.status == "action_required"

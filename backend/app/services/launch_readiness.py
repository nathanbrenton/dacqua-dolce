from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.sales_area import (
    APPROVED_LAUNCH_COUNTRY_CODE,
    APPROVED_LAUNCH_REGION_CODES,
    SalesAreaConfigurationError,
    load_sales_area_policy,
)
from app.models.catalog import (
    InventorySourceKind,
    InventoryStatus,
    Product,
)
from app.models.policy import PolicyKind
from app.services.policies import (
    BASE_REQUIRED_QUOTE_POLICIES,
    POLICY_LABELS,
    current_approved_policy,
    refund_policy_terms,
    refund_policy_terms_summary,
)
from app.services.warranties import warranty_document_is_sale_ready

LaunchReadinessStatus = Literal[
    "ready",
    "action_required",
    "deferred",
]


@dataclass(frozen=True)
class LaunchReadinessCheck:
    key: str
    label: str
    status: LaunchReadinessStatus
    detail: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class LaunchReadinessSnapshot:
    status: LaunchReadinessStatus
    ready_count: int
    action_required_count: int
    deferred_count: int
    checks: tuple[LaunchReadinessCheck, ...]


def _load_commercial_products(db: Session) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .options(
                selectinload(Product.documents),
                selectinload(Product.inventory),
                selectinload(Product.tax_classifications),
            )
            .where(
                Product.active.is_(True),
                Product.online_sale_approved.is_(True),
            )
            .order_by(Product.name, Product.id)
        )
        .unique()
        .all()
    )


def _inventory_observation_is_ready(product: Product) -> bool:
    for observation in product.inventory:
        source_kind = getattr(
            observation.source_kind,
            "value",
            observation.source_kind,
        )
        inventory_status = getattr(
            observation.inventory_status,
            "value",
            observation.inventory_status,
        )
        if (
            source_kind != InventorySourceKind.unspecified.value
            and observation.source_observed_at is not None
            and inventory_status != InventoryStatus.not_tracked.value
        ):
            return True
    return False


def _sales_area_check() -> LaunchReadinessCheck:
    try:
        policy = load_sales_area_policy()
    except SalesAreaConfigurationError as exc:
        return LaunchReadinessCheck(
            key="sales_area",
            label="Sales area",
            status="action_required",
            detail="Sales-area configuration is invalid.",
            evidence=(str(exc),),
        )

    region_codes = sorted(policy.region_codes)
    evidence = (
        f"Mode: {policy.mode}",
        f"Country: {policy.country_code}",
        (
            f"Configured regions ({len(region_codes)}): "
            + (", ".join(region_codes) if region_codes else "none")
        ),
    )
    if not policy.enforcement_enabled:
        return LaunchReadinessCheck(
            key="sales_area",
            label="Sales area",
            status="action_required",
            detail=(
                "Geographic enforcement is disabled. Enable the approved "
                "launch allowlist before relying on geographic sales controls."
            ),
            evidence=evidence,
        )

    missing_regions = sorted(
        APPROVED_LAUNCH_REGION_CODES - policy.region_codes
    )
    unexpected_regions = sorted(
        policy.region_codes - APPROVED_LAUNCH_REGION_CODES
    )
    country_matches = (
        policy.country_code == APPROVED_LAUNCH_COUNTRY_CODE
    )
    if not country_matches or missing_regions or unexpected_regions:
        drift_evidence = list(evidence)
        drift_evidence.append(
            f"Approved launch country: {APPROVED_LAUNCH_COUNTRY_CODE}"
        )
        if not country_matches:
            drift_evidence.append(
                "Configured country does not match the approved launch country."
            )
        if missing_regions:
            drift_evidence.append(
                "Missing approved regions: " + ", ".join(missing_regions)
            )
        if unexpected_regions:
            drift_evidence.append(
                "Unexpected regions: " + ", ".join(unexpected_regions)
            )
        return LaunchReadinessCheck(
            key="sales_area",
            label="Sales area",
            status="action_required",
            detail=(
                "Enabled sales-area configuration does not match the "
                "approved PT35 launch territory."
            ),
            evidence=tuple(drift_evidence),
        )

    return LaunchReadinessCheck(
        key="sales_area",
        label="Sales area",
        status="ready",
        detail=(
            "Geographic sales-area enforcement matches the approved "
            "contiguous-U.S.-plus-DC launch territory."
        ),
        evidence=evidence,
    )


def _policy_check(db: Session) -> LaunchReadinessCheck:
    missing: list[str] = []
    invalid: list[str] = []
    evidence: list[str] = []

    for kind in BASE_REQUIRED_QUOTE_POLICIES:
        policy = current_approved_policy(db, kind=kind)
        label = POLICY_LABELS[kind]
        if policy is None:
            missing.append(label)
            evidence.append(f"{label}: missing approved version")
            continue

        if kind == PolicyKind.refund:
            terms = refund_policy_terms(policy)
            if terms is None:
                invalid.append(label)
                evidence.append(
                    f"{label}: approved version {policy.version}; "
                    "structured return terms are missing or invalid"
                )
                continue
            evidence.append(
                f"{label}: approved version {policy.version}; "
                f"{refund_policy_terms_summary(terms)}"
            )
            continue

        evidence.append(f"{label}: approved version {policy.version}")

    if missing or invalid:
        return LaunchReadinessCheck(
            key="policies",
            label="Required policies",
            status="action_required",
            detail=(
                "One or more policies required for formal-quote presentation "
                "are missing or are not fully configured for launch."
            ),
            evidence=tuple(evidence),
        )

    return LaunchReadinessCheck(
        key="policies",
        label="Required policies",
        status="ready",
        detail=(
            "All base policies required for formal-quote presentation are "
            "approved and the Refund Policy has valid structured terms."
        ),
        evidence=tuple(evidence),
    )


def _warranty_check(products: list[Product]) -> LaunchReadinessCheck:
    if not products:
        return LaunchReadinessCheck(
            key="warranties",
            label="Warranty documents",
            status="action_required",
            detail="No active products are currently approved for online sale.",
            evidence=("Commercial products evaluated: 0",),
        )

    missing = [
        product.name
        for product in products
        if not any(
            warranty_document_is_sale_ready(document)
            for document in product.documents
        )
    ]
    ready_count = len(products) - len(missing)
    evidence = [
        f"Verified public warranty coverage: {ready_count}/{len(products)} products",
    ]
    if missing:
        evidence.append(
            "Missing sale-ready warranty evidence: "
            + ", ".join(missing)
        )
        return LaunchReadinessCheck(
            key="warranties",
            label="Warranty documents",
            status="action_required",
            detail=(
                "Every active online-sale-approved product should have at least "
                "one verified public warranty document before launch."
            ),
            evidence=tuple(evidence),
        )

    return LaunchReadinessCheck(
        key="warranties",
        label="Warranty documents",
        status="ready",
        detail="Every evaluated commercial product has verified public warranty evidence.",
        evidence=tuple(evidence),
    )


def _inventory_check(products: list[Product]) -> LaunchReadinessCheck:
    if not products:
        return LaunchReadinessCheck(
            key="catalog_inventory",
            label="Catalog & inventory",
            status="action_required",
            detail="No active products are currently approved for online sale.",
            evidence=("Commercial products evaluated: 0",),
        )

    incomplete = [
        product.name
        for product in products
        if not _inventory_observation_is_ready(product)
    ]
    ready_count = len(products) - len(incomplete)
    evidence = [
        f"Products with sourced inventory observations: {ready_count}/{len(products)}",
    ]
    if incomplete:
        evidence.append(
            "Inventory source/observation incomplete: "
            + ", ".join(incomplete)
        )
        return LaunchReadinessCheck(
            key="catalog_inventory",
            label="Catalog & inventory",
            status="action_required",
            detail=(
                "Commercial products should have a sourced, timestamped "
                "availability observation before launch."
            ),
            evidence=tuple(evidence),
        )

    return LaunchReadinessCheck(
        key="catalog_inventory",
        label="Catalog & inventory",
        status="ready",
        detail="Commercial products have sourced, timestamped availability observations.",
        evidence=tuple(evidence),
    )


def _payment_check() -> LaunchReadinessCheck:
    return LaunchReadinessCheck(
        key="payment_checkout",
        label="Payment & checkout",
        status="deferred",
        detail=(
            "Hosted-checkout orchestration is provider-neutral, but production "
            "Affinity24 gateway wiring and credentials remain intentionally unconfigured."
        ),
        evidence=(
            "PCI-sensitive card entry remains outside D’Acqua Dolce.",
            "No production payment-provider adapter is selected in application settings.",
        ),
    )


def _tax_check(products: list[Product]) -> LaunchReadinessCheck:
    missing = [
        product.name
        for product in products
        if not any(
            classification.active
            and classification.provider == "stripe_tax"
            and bool(classification.tax_code.strip())
            and bool(classification.source_reference.strip())
            for classification in product.tax_classifications
        )
    ]
    ready_count = len(products) - len(missing)
    evidence = [
        (
            "Stripe Tax classifications recorded: "
            f"{ready_count}/{len(products)} online-sale products"
        ),
        (
            "PT44 supports Stripe Tax test-mode calculation only; "
            "live credentials are rejected by design."
        ),
        (
            "Hosted payment remains blocked unless the order has a current "
            "authoritative automated tax calculation."
        ),
    ]
    if missing:
        evidence.append(
            "Missing tax classification: " + ", ".join(missing)
        )

    return LaunchReadinessCheck(
        key="tax",
        label="Automated sales tax",
        status="action_required",
        detail=(
            "Automated tax is a launch requirement. The provider-neutral "
            "evidence model and Stripe Tax sandbox adapter are implemented, "
            "but product classification, tax registrations, live credentials, "
            "and production commissioning must all be completed before checkout."
        ),
        evidence=tuple(evidence),
    )


def _shipping_insurance_check() -> LaunchReadinessCheck:
    return LaunchReadinessCheck(
        key="shipping_insurance",
        label="Shipping insurance terms",
        status="deferred",
        detail=(
            "Quote pricing and customer accept/decline evidence are implemented, "
            "while provider terms, coverage, rating, and claims handling remain deferred."
        ),
        evidence=(
            "Shipping insurance is a distinct commercial charge.",
            "Customer decision evidence is tied to the formal-quote revision.",
        ),
    )


def build_launch_readiness(db: Session) -> LaunchReadinessSnapshot:
    products = _load_commercial_products(db)
    checks = (
        _sales_area_check(),
        _policy_check(db),
        _warranty_check(products),
        _inventory_check(products),
        _payment_check(),
        _tax_check(products),
        _shipping_insurance_check(),
    )

    ready_count = sum(check.status == "ready" for check in checks)
    action_required_count = sum(
        check.status == "action_required"
        for check in checks
    )
    deferred_count = sum(check.status == "deferred" for check in checks)

    if action_required_count:
        status: LaunchReadinessStatus = "action_required"
    elif deferred_count:
        status = "deferred"
    else:
        status = "ready"

    return LaunchReadinessSnapshot(
        status=status,
        ready_count=ready_count,
        action_required_count=action_required_count,
        deferred_count=deferred_count,
        checks=checks,
    )

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.policy import PolicyDocumentStatus, PolicyKind
from app.schemas.policies import PolicyExportScope, PolicyImportMode
from app.services.policy_portability import (
    build_policy_export_bundle,
    plan_policy_import,
)


def policy(
    *,
    kind: PolicyKind = PolicyKind.terms,
    version: str = "2026-10-01",
    status: PolicyDocumentStatus = PolicyDocumentStatus.approved,
    body: str = "Reviewed terms.",
) -> SimpleNamespace:
    now = datetime(2026, 10, 1, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        kind=kind,
        version=version,
        title="Terms & Policies" if kind == PolicyKind.terms else "Refund Policy",
        body=body,
        structured_terms=(
            {
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
            if kind == PolicyKind.refund
            else None
        ),
        status=status,
        effective_at=now if status == PolicyDocumentStatus.approved else None,
        approved_at=now if status == PolicyDocumentStatus.approved else None,
        created_at=now,
    )


def test_export_all_preserves_policy_history_and_hashes() -> None:
    rows = [
        policy(version="v1", status=PolicyDocumentStatus.retired),
        policy(version="v2", status=PolicyDocumentStatus.approved),
        policy(version="v3", status=PolicyDocumentStatus.draft),
    ]

    bundle = build_policy_export_bundle(rows, scope=PolicyExportScope.all)

    assert bundle.format == "dacqua_dolce_policy_bundle"
    assert bundle.format_version == 1
    assert [entry.version for entry in bundle.policies] == ["v1", "v2", "v3"]
    assert all(len(entry.content_sha256) == 64 for entry in bundle.policies)
    assert len(bundle.bundle_sha256) == 64


def test_approved_export_contains_only_effective_versions() -> None:
    rows = [
        policy(version="v1", status=PolicyDocumentStatus.retired),
        policy(version="v2", status=PolicyDocumentStatus.approved),
        policy(version="v3", status=PolicyDocumentStatus.draft),
    ]

    bundle = build_policy_export_bundle(
        rows,
        scope=PolicyExportScope.approved_effective,
    )

    assert [entry.version for entry in bundle.policies] == ["v2"]


def test_draft_only_import_adds_missing_and_skips_matching_content() -> None:
    source = policy(version="v2", status=PolicyDocumentStatus.approved)
    bundle = build_policy_export_bundle([source], scope=PolicyExportScope.all)

    missing = plan_policy_import(
        [],
        bundle=bundle,
        mode=PolicyImportMode.draft_only,
        preserve_allowed=False,
    )
    assert missing.additions == 1
    assert missing.conflicts == 0
    assert missing.actions[0].action == "add"
    assert "draft" in missing.actions[0].detail.lower()

    matching = plan_policy_import(
        [source],
        bundle=bundle,
        mode=PolicyImportMode.draft_only,
        preserve_allowed=False,
    )
    assert matching.skips == 1
    assert matching.actions[0].action == "skip"


def test_import_flags_same_kind_version_with_different_content() -> None:
    source = policy(version="v2", body="Source text.")
    destination = policy(version="v2", body="Different destination text.")
    bundle = build_policy_export_bundle([source], scope=PolicyExportScope.all)

    report = plan_policy_import(
        [destination],
        bundle=bundle,
        mode=PolicyImportMode.draft_only,
        preserve_allowed=False,
    )

    assert report.conflicts == 1
    assert report.actions[0].action == "conflict"


def test_lifecycle_preservation_is_explicitly_gated() -> None:
    bundle = build_policy_export_bundle(
        [policy()],
        scope=PolicyExportScope.all,
    )

    with pytest.raises(HTTPException) as exc:
        plan_policy_import(
            [],
            bundle=bundle,
            mode=PolicyImportMode.preserve_lifecycle,
            preserve_allowed=False,
        )

    assert exc.value.status_code == 409
    assert "non-production" in exc.value.detail


def test_lifecycle_preview_reports_sync_and_destination_retirement() -> None:
    source = policy(version="v2", status=PolicyDocumentStatus.approved)
    destination_matching = policy(version="v2", status=PolicyDocumentStatus.draft)
    destination_old = policy(version="v1", status=PolicyDocumentStatus.approved)
    bundle = build_policy_export_bundle([source], scope=PolicyExportScope.all)

    report = plan_policy_import(
        [destination_matching, destination_old],
        bundle=bundle,
        mode=PolicyImportMode.preserve_lifecycle,
        preserve_allowed=True,
    )

    assert report.lifecycle_updates == 1
    assert report.destination_retirements == 1
    assert report.conflicts == 0


def test_tampered_bundle_is_rejected() -> None:
    bundle = build_policy_export_bundle(
        [policy()],
        scope=PolicyExportScope.all,
    )
    bundle.policies[0].body = "Tampered after export."

    with pytest.raises(HTTPException) as exc:
        plan_policy_import(
            [],
            bundle=bundle,
            mode=PolicyImportMode.draft_only,
            preserve_allowed=False,
        )

    assert exc.value.status_code == 422
    assert "hash mismatch" in exc.value.detail

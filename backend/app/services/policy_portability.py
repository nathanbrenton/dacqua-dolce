from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import User
from app.models.policy import PolicyDocument, PolicyDocumentStatus, PolicyKind
from app.schemas.policies import (
    PolicyExportBundle,
    PolicyExportEntry,
    PolicyExportScope,
    PolicyImportAction,
    PolicyImportMode,
    PolicyImportReport,
    RefundPolicyTerms,
)
from app.services.audit import record_audit_event

POLICY_BUNDLE_FORMAT = "dacqua_dolce_policy_bundle"
POLICY_BUNDLE_VERSION = 1
PRESERVE_LIFECYCLE_ENV = "DACQUA_POLICY_IMPORT_ALLOW_LIFECYCLE_PRESERVATION"


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _structured_terms_hash(value: dict[str, object] | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _content_hash(
    *,
    kind: PolicyKind,
    version: str,
    title: str,
    body: str,
    structured_terms: dict[str, object] | None,
) -> str:
    payload = {
        "kind": kind.value,
        "version": version,
        "title": title,
        "body": body,
        "structured_terms": structured_terms,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _bundle_fingerprint(entries: list[PolicyExportEntry]) -> str:
    payload = [
        {
            "kind": entry.kind.value,
            "version": entry.version,
            "content_sha256": entry.content_sha256,
            "status": entry.status.value,
            "effective_at": entry.effective_at.isoformat() if entry.effective_at else None,
            "approved_at": entry.approved_at.isoformat() if entry.approved_at else None,
        }
        for entry in entries
    ]
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _entry_from_policy(row: PolicyDocument) -> PolicyExportEntry:
    structured_terms = (
        dict(row.structured_terms)
        if isinstance(row.structured_terms, dict)
        else None
    )
    return PolicyExportEntry(
        kind=row.kind,
        version=row.version,
        title=row.title,
        body=row.body,
        structured_terms=structured_terms,
        status=row.status,
        effective_at=row.effective_at,
        approved_at=row.approved_at,
        source_created_at=row.created_at,
        content_sha256=_content_hash(
            kind=row.kind,
            version=row.version,
            title=row.title,
            body=row.body,
            structured_terms=structured_terms,
        ),
        structured_terms_sha256=_structured_terms_hash(structured_terms),
    )


def build_policy_export_bundle(
    rows: Iterable[PolicyDocument],
    *,
    scope: PolicyExportScope,
) -> PolicyExportBundle:
    selected = list(rows)
    if scope == PolicyExportScope.approved_effective:
        selected = [
            row for row in selected
            if row.status == PolicyDocumentStatus.approved
        ]

    entries = [
        _entry_from_policy(row)
        for row in sorted(selected, key=lambda row: (row.kind.value, row.version))
    ]
    return PolicyExportBundle(
        format=POLICY_BUNDLE_FORMAT,
        format_version=POLICY_BUNDLE_VERSION,
        scope=scope,
        exported_at=datetime.now(UTC),
        policies=entries,
        bundle_sha256=_bundle_fingerprint(entries),
    )


def export_policy_bundle(
    db: Session,
    *,
    scope: PolicyExportScope,
) -> PolicyExportBundle:
    rows = db.scalars(
        select(PolicyDocument).order_by(
            PolicyDocument.kind,
            PolicyDocument.version,
        )
    ).all()
    return build_policy_export_bundle(rows, scope=scope)


def lifecycle_preservation_allowed() -> bool:
    value = os.environ.get(PRESERVE_LIFECYCLE_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _validate_entry(entry: PolicyExportEntry) -> None:
    structured_terms = (
        dict(entry.structured_terms)
        if entry.structured_terms is not None
        else None
    )
    expected_content = _content_hash(
        kind=entry.kind,
        version=entry.version,
        title=entry.title,
        body=entry.body,
        structured_terms=structured_terms,
    )
    if entry.content_sha256 != expected_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Policy bundle content hash mismatch for "
                f"{entry.kind.value}/{entry.version}."
            ),
        )

    expected_structured = _structured_terms_hash(structured_terms)
    if entry.structured_terms_sha256 != expected_structured:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Policy bundle structured-terms hash mismatch for "
                f"{entry.kind.value}/{entry.version}."
            ),
        )

    if entry.kind == PolicyKind.refund and structured_terms is not None:
        try:
            RefundPolicyTerms.model_validate(structured_terms)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Refund structured terms are invalid for version "
                    f"{entry.version}."
                ),
            ) from exc
    elif entry.kind != PolicyKind.refund and structured_terms is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Structured refund terms may only be attached to the Refund Policy.",
        )


def validate_policy_bundle(bundle: PolicyExportBundle) -> None:
    if bundle.format != POLICY_BUNDLE_FORMAT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported policy bundle format.",
        )
    if bundle.format_version != POLICY_BUNDLE_VERSION:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported policy bundle version.",
        )

    keys: set[tuple[PolicyKind, str]] = set()
    approved_counts: Counter[PolicyKind] = Counter()
    for entry in bundle.policies:
        key = (entry.kind, entry.version)
        if key in keys:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Policy bundle contains duplicate version "
                    f"{entry.kind.value}/{entry.version}."
                ),
            )
        keys.add(key)
        _validate_entry(entry)
        if entry.status == PolicyDocumentStatus.approved:
            approved_counts[entry.kind] += 1

    duplicate_approved = [
        kind.value for kind, count in approved_counts.items() if count > 1
    ]
    if duplicate_approved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Policy bundle contains more than one approved version for: "
                + ", ".join(sorted(duplicate_approved))
                + "."
            ),
        )

    expected_bundle_hash = _bundle_fingerprint(bundle.policies)
    if bundle.bundle_sha256 != expected_bundle_hash:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Policy bundle fingerprint does not match its contents.",
        )


def _content_matches(row: PolicyDocument, entry: PolicyExportEntry) -> bool:
    structured_terms = (
        dict(row.structured_terms)
        if isinstance(row.structured_terms, dict)
        else None
    )
    return _content_hash(
        kind=row.kind,
        version=row.version,
        title=row.title,
        body=row.body,
        structured_terms=structured_terms,
    ) == entry.content_sha256


def _lifecycle_matches(row: PolicyDocument, entry: PolicyExportEntry) -> bool:
    return (
        row.status == entry.status
        and row.effective_at == entry.effective_at
        and row.approved_at == entry.approved_at
    )


def plan_policy_import(
    existing_rows: Iterable[PolicyDocument],
    *,
    bundle: PolicyExportBundle,
    mode: PolicyImportMode,
    preserve_allowed: bool | None = None,
) -> PolicyImportReport:
    validate_policy_bundle(bundle)
    if preserve_allowed is None:
        preserve_allowed = lifecycle_preservation_allowed()
    if mode == PolicyImportMode.preserve_lifecycle and not preserve_allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Lifecycle-preserving policy import is disabled in this environment. "
                f"Enable {PRESERVE_LIFECYCLE_ENV}=true only in an intended "
                "non-production environment."
            ),
        )

    existing = {(row.kind, row.version): row for row in existing_rows}
    actions: list[PolicyImportAction] = []
    incoming_approved = {
        entry.kind: entry.version
        for entry in bundle.policies
        if entry.status == PolicyDocumentStatus.approved
    }

    for entry in bundle.policies:
        key = (entry.kind, entry.version)
        row = existing.get(key)
        if row is None:
            actions.append(
                PolicyImportAction(
                    kind=entry.kind,
                    version=entry.version,
                    action="add",
                    detail=(
                        "Create as source lifecycle state."
                        if mode == PolicyImportMode.preserve_lifecycle
                        else "Create as draft; source lifecycle is not promoted."
                    ),
                )
            )
            continue
        if not _content_matches(row, entry):
            actions.append(
                PolicyImportAction(
                    kind=entry.kind,
                    version=entry.version,
                    action="conflict",
                    detail="Destination has the same kind/version with different content.",
                )
            )
            continue
        if mode == PolicyImportMode.preserve_lifecycle and not _lifecycle_matches(row, entry):
            actions.append(
                PolicyImportAction(
                    kind=entry.kind,
                    version=entry.version,
                    action="update_lifecycle",
                    detail="Content matches; synchronize lifecycle/effective metadata.",
                )
            )
            continue
        actions.append(
            PolicyImportAction(
                kind=entry.kind,
                version=entry.version,
                action="skip",
                detail="Exact policy content already exists.",
            )
        )

    if mode == PolicyImportMode.preserve_lifecycle:
        incoming_keys = {(entry.kind, entry.version) for entry in bundle.policies}
        for row in existing.values():
            source_approved_version = incoming_approved.get(row.kind)
            if (
                row.status == PolicyDocumentStatus.approved
                and source_approved_version is not None
                and row.version != source_approved_version
                and (row.kind, row.version) not in incoming_keys
            ):
                actions.append(
                    PolicyImportAction(
                        kind=row.kind,
                        version=row.version,
                        action="retire_destination_approved",
                        detail=(
                            "Retire destination-only approved version so the incoming "
                            "approved version can become authoritative in this "
                            "non-production environment."
                        ),
                    )
                )

    counts = Counter(action.action for action in actions)
    return PolicyImportReport(
        mode=mode,
        source_scope=bundle.scope,
        bundle_sha256=bundle.bundle_sha256,
        lifecycle_preservation_allowed=preserve_allowed,
        additions=counts["add"],
        skips=counts["skip"],
        conflicts=counts["conflict"],
        lifecycle_updates=counts["update_lifecycle"],
        destination_retirements=counts["retire_destination_approved"],
        actions=actions,
    )


def preview_policy_import(
    db: Session,
    *,
    bundle: PolicyExportBundle,
    mode: PolicyImportMode,
) -> PolicyImportReport:
    rows = db.scalars(select(PolicyDocument)).all()
    return plan_policy_import(rows, bundle=bundle, mode=mode)


def apply_policy_import(
    db: Session,
    *,
    bundle: PolicyExportBundle,
    mode: PolicyImportMode,
    actor_user: User,
) -> PolicyImportReport:
    rows = list(db.scalars(select(PolicyDocument)).all())
    report = plan_policy_import(rows, bundle=bundle, mode=mode)
    if report.conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy import has content conflicts. Resolve them before applying.",
        )

    existing = {(row.kind, row.version): row for row in rows}
    entry_by_key = {(entry.kind, entry.version): entry for entry in bundle.policies}

    if mode == PolicyImportMode.preserve_lifecycle:
        incoming_approved = {
            entry.kind: entry.version
            for entry in bundle.policies
            if entry.status == PolicyDocumentStatus.approved
        }
        for row in existing.values():
            incoming_version = incoming_approved.get(row.kind)
            if (
                row.status == PolicyDocumentStatus.approved
                and incoming_version is not None
                and row.version != incoming_version
            ):
                row.status = PolicyDocumentStatus.retired
                row.approved_at = None
                row.effective_at = None
                row.approved_by_user_id = None
        db.flush()

    for action in report.actions:
        if action.action not in {"add", "update_lifecycle"}:
            continue
        entry = entry_by_key[(action.kind, action.version)]
        row = existing.get((entry.kind, entry.version))
        if row is None:
            row = PolicyDocument(
                kind=entry.kind,
                version=entry.version,
                title=entry.title,
                body=entry.body,
                structured_terms=(
                    dict(entry.structured_terms)
                    if entry.structured_terms is not None
                    else None
                ),
                status=(
                    entry.status
                    if mode == PolicyImportMode.preserve_lifecycle
                    else PolicyDocumentStatus.draft
                ),
                effective_at=(
                    entry.effective_at
                    if mode == PolicyImportMode.preserve_lifecycle
                    else None
                ),
                approved_at=(
                    entry.approved_at
                    if mode == PolicyImportMode.preserve_lifecycle
                    else None
                ),
                approved_by_user_id=None,
                created_by_user_id=actor_user.id,
                created_at=entry.source_created_at,
            )
            db.add(row)
            existing[(entry.kind, entry.version)] = row
        elif mode == PolicyImportMode.preserve_lifecycle:
            row.status = entry.status
            row.effective_at = entry.effective_at
            row.approved_at = entry.approved_at
            row.approved_by_user_id = None

    db.flush()
    record_audit_event(
        db,
        action="policy_bundle.imported",
        entity_type="policy_bundle",
        entity_id=bundle.bundle_sha256,
        actor_user_id=actor_user.id,
        metadata={
            "mode": mode.value,
            "source_scope": bundle.scope.value,
            "additions": report.additions,
            "skips": report.skips,
            "lifecycle_updates": report.lifecycle_updates,
            "destination_retirements": report.destination_retirements,
        },
    )
    return report

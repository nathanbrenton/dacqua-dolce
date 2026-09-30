from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import User
from app.models.policy import (
    FormalQuotePolicySnapshot,
    PolicyDocument,
    PolicyDocumentStatus,
    PolicyKind,
)
from app.models.quote import CommercialChargeKind, FormalQuote
from app.services.audit import record_audit_event

BASE_REQUIRED_QUOTE_POLICIES = (
    PolicyKind.terms,
    PolicyKind.shipping,
    PolicyKind.cancellation,
    PolicyKind.refund,
    PolicyKind.warranty,
)

POLICY_LABELS = {
    PolicyKind.privacy: "Privacy",
    PolicyKind.terms: "Terms & Policies",
    PolicyKind.shipping: "Shipping Policy",
    PolicyKind.cancellation: "Cancellation Policy",
    PolicyKind.refund: "Refund Policy",
    PolicyKind.warranty: "Warranty",
    PolicyKind.installation: "Installation Terms",
}


def current_approved_policy(db: Session, *, kind: PolicyKind) -> PolicyDocument | None:
    return db.scalar(
        select(PolicyDocument)
        .where(
            PolicyDocument.kind == kind,
            PolicyDocument.status == PolicyDocumentStatus.approved,
        )
        .order_by(PolicyDocument.approved_at.desc())
    )


def create_policy_draft(
    db: Session,
    *,
    kind: PolicyKind,
    version: str,
    title: str,
    body: str,
    actor_user: User,
) -> PolicyDocument:
    version = version.strip()
    title = title.strip()
    body = body.strip()
    if not version or not title or not body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Policy version, title, and body are required.",
        )

    existing = db.scalar(
        select(PolicyDocument.id).where(
            PolicyDocument.kind == kind,
            PolicyDocument.version == version,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That policy version already exists.",
        )

    row = PolicyDocument(
        kind=kind,
        version=version,
        title=title,
        body=body,
        status=PolicyDocumentStatus.draft,
        created_by_user_id=actor_user.id,
    )
    db.add(row)
    db.flush()
    record_audit_event(
        db,
        action="policy_document.created",
        entity_type="policy_document",
        entity_id=str(row.id),
        actor_user_id=actor_user.id,
        metadata={"kind": kind.value, "version": version},
    )
    return row


def approve_policy_document(
    db: Session,
    *,
    policy: PolicyDocument,
    actor_user: User,
) -> PolicyDocument:
    if policy.status != PolicyDocumentStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a draft policy version can be approved.",
        )

    now = datetime.now(UTC)
    current = current_approved_policy(db, kind=policy.kind)
    if current is not None and current.id != policy.id:
        current.status = PolicyDocumentStatus.retired
        db.flush()

    policy.status = PolicyDocumentStatus.approved
    policy.approved_at = now
    policy.effective_at = now
    policy.approved_by_user_id = actor_user.id
    db.flush()

    record_audit_event(
        db,
        action="policy_document.approved",
        entity_type="policy_document",
        entity_id=str(policy.id),
        actor_user_id=actor_user.id,
        metadata={"kind": policy.kind.value, "version": policy.version},
    )
    return policy


def required_policy_kinds(formal_quote: FormalQuote) -> tuple[PolicyKind, ...]:
    kinds = list(BASE_REQUIRED_QUOTE_POLICIES)
    if any(
        charge.kind == CommercialChargeKind.installation.value
        for charge in formal_quote.charges
    ):
        kinds.append(PolicyKind.installation)
    return tuple(kinds)


def snapshot_quote_policies(
    db: Session,
    *,
    formal_quote: FormalQuote,
) -> list[FormalQuotePolicySnapshot]:
    if formal_quote.policy_snapshots:
        return list(formal_quote.policy_snapshots)

    documents: list[PolicyDocument] = []
    missing: list[str] = []
    for kind in required_policy_kinds(formal_quote):
        policy = current_approved_policy(db, kind=kind)
        if policy is None:
            missing.append(POLICY_LABELS[kind])
        else:
            documents.append(policy)

    if missing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Approved launch policies are required before presentation: "
                + ", ".join(missing)
                + "."
            ),
        )

    snapshots: list[FormalQuotePolicySnapshot] = []
    for sort_order, policy in enumerate(documents):
        digest = hashlib.sha256(policy.body.encode("utf-8")).hexdigest()
        snapshot = FormalQuotePolicySnapshot(
            formal_quote_id=formal_quote.id,
            policy_document_id=policy.id,
            kind=policy.kind,
            version_snapshot=policy.version,
            title_snapshot=policy.title,
            body_snapshot=policy.body,
            content_sha256=digest,
            effective_at_snapshot=policy.effective_at,
            sort_order=sort_order,
        )
        db.add(snapshot)
        snapshots.append(snapshot)

    db.flush()
    formal_quote.policy_snapshots = snapshots
    return snapshots

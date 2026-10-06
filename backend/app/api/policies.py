from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies.auth import CurrentUser, DatabaseSession
from app.models.policy import PolicyDocument, PolicyKind
from app.schemas.policies import (
    PolicyDocumentCreate,
    PolicyDocumentRead,
    PolicyExportBundle,
    PolicyExportScope,
    PolicyImportReport,
    PolicyImportRequest,
    PolicyPublicRead,
)
from app.services.operations_access import require_administration, require_operations
from app.services.policies import (
    POLICY_LABELS,
    approve_policy_document,
    create_policy_draft,
    current_approved_policy,
)
from app.services.policy_portability import (
    apply_policy_import,
    export_policy_bundle,
    preview_policy_import,
)

public_router = APIRouter(prefix="/policies", tags=["policies"])
operations_router = APIRouter(prefix="/operations/policies", tags=["operations"])


def policy_document_read(row: PolicyDocument) -> PolicyDocumentRead:
    return PolicyDocumentRead(
        id=row.id,
        kind=row.kind,
        version=row.version,
        title=row.title,
        body=row.body,
        refund_terms=(
            row.structured_terms
            if row.kind == PolicyKind.refund
            else None
        ),
        status=row.status,
        effective_at=row.effective_at,
        approved_at=row.approved_at,
        approved_by_user_id=row.approved_by_user_id,
        created_by_user_id=row.created_by_user_id,
        created_at=row.created_at,
    )


@public_router.get(
    "/{kind}",
    response_model=PolicyPublicRead,
)
def get_public_policy(
    kind: PolicyKind,
    db: DatabaseSession,
) -> PolicyPublicRead:
    row = current_approved_policy(db, kind=kind)
    if row is None:
        return PolicyPublicRead(
            kind=kind,
            approved=False,
            title=POLICY_LABELS[kind],
        )

    return PolicyPublicRead(
        kind=kind,
        approved=True,
        title=row.title,
        version=row.version,
        body=row.body,
        effective_at=row.effective_at,
    )


@operations_router.get(
    "",
    response_model=list[PolicyDocumentRead],
)
def get_operations_policies(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[PolicyDocumentRead]:
    require_operations(db, user=current_user)
    rows = db.scalars(
        select(PolicyDocument).order_by(
            PolicyDocument.kind,
            PolicyDocument.created_at.desc(),
        )
    ).all()
    return [policy_document_read(row) for row in rows]


@operations_router.post(
    "",
    response_model=PolicyDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_operations_policy(
    payload: PolicyDocumentCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PolicyDocumentRead:
    require_administration(db, user=current_user)
    row = create_policy_draft(
        db,
        kind=payload.kind,
        version=payload.version,
        title=payload.title,
        body=payload.body,
        actor_user=current_user,
        structured_terms=(
            payload.refund_terms.model_dump()
            if payload.refund_terms is not None
            else None
        ),
    )
    db.commit()
    db.refresh(row)
    return policy_document_read(row)


@operations_router.post(
    "/{policy_id}/approve",
    response_model=PolicyDocumentRead,
)
def approve_operations_policy(
    policy_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PolicyDocumentRead:
    require_administration(db, user=current_user)
    row = db.get(PolicyDocument, policy_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy version not found.",
        )

    approve_policy_document(
        db,
        policy=row,
        actor_user=current_user,
    )
    db.commit()
    db.refresh(row)
    return policy_document_read(row)


@operations_router.get(
    "/export",
    response_model=PolicyExportBundle,
)
def export_operations_policies(
    db: DatabaseSession,
    current_user: CurrentUser,
    scope: PolicyExportScope = PolicyExportScope.all,
) -> PolicyExportBundle:
    require_operations(db, user=current_user)
    return export_policy_bundle(db, scope=scope)


@operations_router.post(
    "/import/preview",
    response_model=PolicyImportReport,
)
def preview_operations_policy_import(
    payload: PolicyImportRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PolicyImportReport:
    require_administration(db, user=current_user)
    return preview_policy_import(
        db,
        bundle=payload.bundle,
        mode=payload.mode,
    )


@operations_router.post(
    "/import/apply",
    response_model=PolicyImportReport,
)
def apply_operations_policy_import(
    payload: PolicyImportRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> PolicyImportReport:
    require_administration(db, user=current_user)
    report = apply_policy_import(
        db,
        bundle=payload.bundle,
        mode=payload.mode,
        actor_user=current_user,
    )
    db.commit()
    return report

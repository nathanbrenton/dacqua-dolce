from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies.auth import CurrentUser, DatabaseSession
from app.models.policy import PolicyDocument, PolicyKind
from app.schemas.policies import (
    PolicyDocumentCreate,
    PolicyDocumentRead,
    PolicyPublicRead,
)
from app.services.operations_access import require_administration, require_operations
from app.services.policies import (
    POLICY_LABELS,
    approve_policy_document,
    create_policy_draft,
    current_approved_policy,
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

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.policy import PolicyDocumentStatus, PolicyKind


class PolicyPublicRead(BaseModel):
    kind: PolicyKind
    approved: bool
    title: str
    version: str | None = None
    body: str | None = None
    effective_at: datetime | None = None


class PolicyDocumentCreate(BaseModel):
    kind: PolicyKind
    version: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=100_000)

    @field_validator("version", "title", "body")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be blank.")
        return cleaned


class PolicyDocumentRead(BaseModel):
    id: uuid.UUID
    kind: PolicyKind
    version: str
    title: str
    body: str
    status: PolicyDocumentStatus
    effective_at: datetime | None
    approved_at: datetime | None
    approved_by_user_id: uuid.UUID | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime


class FormalQuotePolicySnapshotRead(BaseModel):
    id: uuid.UUID
    kind: PolicyKind
    version: str
    title: str
    body: str
    content_sha256: str
    effective_at: datetime | None


class FormalQuoteApprovalRequest(BaseModel):
    policy_snapshot_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)

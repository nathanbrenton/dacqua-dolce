from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.policy import PolicyDocumentStatus, PolicyKind


class RefundPolicyTerms(BaseModel):
    eligibility_mode: Literal[
        "fixed_window",
        "case_by_case",
        "fixed_window_with_exception",
    ]
    return_window_days: int | None = Field(default=None, ge=1, le=365)
    restocking_mode: Literal[
        "fixed_percentage",
        "case_by_case",
    ]
    restocking_fee_basis_points: int | None = Field(
        default=None,
        ge=1,
        le=10_000,
    )
    merchandise_condition: Literal["new_uninstalled"] = "new_uninstalled"
    customer_pays_return_shipping_by_default: bool = True
    outbound_shipping_refund_rule: Literal[
        "nonrefundable_with_error_defect_or_discretion_exception"
    ] = "nonrefundable_with_error_defect_or_discretion_exception"
    acknowledgement_required: bool = True

    @model_validator(mode="after")
    def validate_modes(self) -> RefundPolicyTerms:
        if self.eligibility_mode == "case_by_case":
            if self.return_window_days is not None:
                raise ValueError(
                    "Case-by-case return eligibility must not set a fixed return window."
                )
        elif self.return_window_days is None:
            raise ValueError(
                "Fixed-window return eligibility requires return_window_days."
            )

        if self.restocking_mode == "case_by_case":
            if self.restocking_fee_basis_points is not None:
                raise ValueError(
                    "Case-by-case restocking must not set a fixed percentage."
                )
        elif self.restocking_fee_basis_points is None:
            raise ValueError(
                "Fixed-percentage restocking requires restocking_fee_basis_points."
            )

        return self


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
    refund_terms: RefundPolicyTerms | None = None

    @field_validator("version", "title", "body")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be blank.")
        return cleaned

    @model_validator(mode="after")
    def validate_structured_terms(self) -> PolicyDocumentCreate:
        if self.refund_terms is not None and self.kind != PolicyKind.refund:
            raise ValueError(
                "Structured refund terms may only be attached to the Refund Policy."
            )
        return self


class PolicyDocumentRead(BaseModel):
    id: uuid.UUID
    kind: PolicyKind
    version: str
    title: str
    body: str
    refund_terms: RefundPolicyTerms | None = None
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
    refund_terms: RefundPolicyTerms | None = None
    content_sha256: str
    structured_terms_sha256: str | None = None
    effective_at: datetime | None


class FormalQuoteApprovalRequest(BaseModel):
    policy_snapshot_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


class PolicyExportScope(StrEnum):
    all = "all"
    approved_effective = "approved_effective"


class PolicyImportMode(StrEnum):
    draft_only = "draft_only"
    preserve_lifecycle = "preserve_lifecycle"


class PolicyExportEntry(BaseModel):
    kind: PolicyKind
    version: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=100_000)
    structured_terms: dict[str, object] | None = None
    status: PolicyDocumentStatus
    effective_at: datetime | None = None
    approved_at: datetime | None = None
    source_created_at: datetime
    content_sha256: str = Field(min_length=64, max_length=64)
    structured_terms_sha256: str | None = Field(default=None, min_length=64, max_length=64)


class PolicyExportBundle(BaseModel):
    format: str
    format_version: int
    scope: PolicyExportScope
    exported_at: datetime
    policies: list[PolicyExportEntry]
    bundle_sha256: str = Field(min_length=64, max_length=64)


class PolicyImportAction(BaseModel):
    kind: PolicyKind
    version: str
    action: Literal[
        "add",
        "skip",
        "conflict",
        "update_lifecycle",
        "retire_destination_approved",
    ]
    detail: str


class PolicyImportRequest(BaseModel):
    bundle: PolicyExportBundle
    mode: PolicyImportMode = PolicyImportMode.draft_only


class PolicyImportReport(BaseModel):
    mode: PolicyImportMode
    source_scope: PolicyExportScope
    bundle_sha256: str
    lifecycle_preservation_allowed: bool
    additions: int
    skips: int
    conflicts: int
    lifecycle_updates: int
    destination_retirements: int
    actions: list[PolicyImportAction]

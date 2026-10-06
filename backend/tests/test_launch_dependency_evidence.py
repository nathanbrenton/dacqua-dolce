from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.launch import LaunchDependencyEvidence
from app.schemas.operations import LaunchDependencyEvidenceUpdateRequest


def test_launch_dependency_evidence_is_tracking_only() -> None:
    assert LaunchDependencyEvidence.__tablename__ == "launch_dependency_evidence"
    columns = LaunchDependencyEvidence.__table__.columns
    assert "commerce_checkout_allowed" not in columns
    assert "launch_phase" not in columns
    assert "api_key" not in columns
    assert "credential" not in columns


def test_launch_dependency_evidence_update_normalizes_optional_text() -> None:
    payload = LaunchDependencyEvidenceUpdateRequest(
        tracking_status="in_progress",
        source_reference="  CPA meeting notes / 2026-10-06  ",
        evidence_received_at=datetime(2026, 10, 6, 14, 0, tzinfo=UTC),
        internal_notes="  Awaiting follow-up documents.  ",
    )

    assert payload.source_reference == "CPA meeting notes / 2026-10-06"
    assert payload.internal_notes == "Awaiting follow-up documents."
    assert payload.evidence_received_at is not None


def test_launch_dependency_evidence_blank_optional_text_becomes_none() -> None:
    payload = LaunchDependencyEvidenceUpdateRequest(
        tracking_status="action_required",
        source_reference="   ",
        internal_notes="   ",
    )

    assert payload.source_reference is None
    assert payload.internal_notes is None


def test_launch_dependency_evidence_status_is_constrained() -> None:
    with pytest.raises(ValidationError):
        LaunchDependencyEvidenceUpdateRequest(
            tracking_status="ready",  # type: ignore[arg-type]
        )


def test_launch_dependency_evidence_requires_timezone_when_date_is_supplied() -> None:
    with pytest.raises(ValidationError):
        LaunchDependencyEvidenceUpdateRequest(
            tracking_status="evidence_received",
            evidence_received_at=datetime(2026, 10, 6, 14, 0),
        )

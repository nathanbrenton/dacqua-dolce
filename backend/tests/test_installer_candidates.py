import pytest
from pydantic import ValidationError

from app.models.commerce import InstallerCandidate
from app.schemas.operations import (
    InstallerCandidateCreateRequest,
    InstallerCandidateUpdateRequest,
)


def test_installer_candidate_table_is_internal_record() -> None:
    assert InstallerCandidate.__tablename__ == "installer_candidates"
    assert "public" not in InstallerCandidate.__table__.columns
    assert "approved" not in InstallerCandidate.__table__.columns
    assert "licensed" not in InstallerCandidate.__table__.columns


def test_installer_candidate_create_normalizes_contact_fields() -> None:
    payload = InstallerCandidateCreateRequest(
        business_name="  Example Plumbing  ",
        contact_name="  Jane Doe  ",
        email="  JANE@EXAMPLE.COM  ",
        service_area_notes="  Orange County research lead  ",
        source_reference="  Manufacturer suggestion  ",
    )

    assert payload.business_name == "Example Plumbing"
    assert payload.contact_name == "Jane Doe"
    assert payload.email == "jane@example.com"
    assert payload.service_area_notes == "Orange County research lead"
    assert payload.source_reference == "Manufacturer suggestion"
    assert payload.status == "researching"


def test_installer_candidate_blank_optional_fields_become_none() -> None:
    payload = InstallerCandidateCreateRequest(
        business_name="Example Plumbing",
        contact_name="   ",
        website="   ",
        internal_notes="   ",
    )

    assert payload.contact_name is None
    assert payload.website is None
    assert payload.internal_notes is None


def test_installer_candidate_status_is_constrained() -> None:
    with pytest.raises(ValidationError):
        InstallerCandidateCreateRequest(
            business_name="Example Plumbing",
            status="approved",  # type: ignore[arg-type]
        )


def test_installer_candidate_update_preserves_omitted_fields() -> None:
    payload = InstallerCandidateUpdateRequest(status="contacted")

    assert payload.model_dump(exclude_unset=True) == {"status": "contacted"}

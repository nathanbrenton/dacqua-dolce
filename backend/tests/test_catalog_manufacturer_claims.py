from datetime import UTC, datetime, timedelta

from app.api.catalog import public_manufacturer_claim_reads
from app.models.catalog import ApprovedProductClaim


def make_claim(
    *,
    text: str,
    source: str = "manufacturer/spec-sheet",
    active: bool = True,
    approved: bool = True,
    expires_at: datetime | None = None,
) -> ApprovedProductClaim:
    return ApprovedProductClaim(
        claim_text=text,
        source_reference=source,
        active=active,
        approved_at=(datetime.now(UTC) if approved else None),
        expires_at=expires_at,
    )


def test_public_manufacturer_claims_require_source_and_current_approval() -> None:
    result = public_manufacturer_claim_reads(
        [
            make_claim(text="Current supported statement"),
            make_claim(text="Missing source", source="   "),
            make_claim(text="Not approved", approved=False),
            make_claim(text="Retired", active=False),
            make_claim(
                text="Expired",
                expires_at=datetime.now(UTC) - timedelta(days=1),
            ),
        ]
    )

    assert [claim.claim_text for claim in result] == ["Current supported statement"]
    assert result[0].source_reference == "manufacturer/spec-sheet"
    assert result[0].provenance_label == "Manufacturer-stated"


def test_public_manufacturer_claim_does_not_claim_independent_verification() -> None:
    result = public_manufacturer_claim_reads(
        [make_claim(text="Manufacturer performance statement")]
    )

    payload = result[0].model_dump()
    assert payload["provenance_label"] == "Manufacturer-stated"
    assert "verified" not in payload

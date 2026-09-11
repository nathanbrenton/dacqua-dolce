from datetime import UTC, datetime

from app.api.catalog import public_specification_reads
from app.models.catalog import ProductSpecification


def make_specification(
    *,
    spec_key: str,
    label: str,
    value_text: str,
    unit: str | None = None,
    public: bool = True,
    active: bool = True,
    verified: bool = True,
    sort_order: int = 0,
) -> ProductSpecification:
    return ProductSpecification(
        spec_key=spec_key,
        label=label,
        value_text=value_text,
        unit=unit,
        source_reference="internal/source-reference",
        public=public,
        active=active,
        verified_at=(
            datetime.now(UTC)
            if verified
            else None
        ),
        sort_order=sort_order,
    )


def test_public_specifications_require_public_active_and_verified() -> None:
    specifications = [
        make_specification(
            spec_key="media_volume",
            label="Media Volume",
            value_text="1.5",
            unit="cu ft",
            sort_order=20,
        ),
        make_specification(
            spec_key="internal_note",
            label="Internal Note",
            value_text="Private",
            public=False,
        ),
        make_specification(
            spec_key="unverified",
            label="Unverified",
            value_text="Pending",
            verified=False,
        ),
        make_specification(
            spec_key="inactive",
            label="Inactive",
            value_text="Old",
            active=False,
        ),
        make_specification(
            spec_key="valve_type",
            label="Valve Type",
            value_text="Pass-Through",
            sort_order=10,
        ),
    ]

    result = public_specification_reads(specifications)

    assert [
        specification.spec_key
        for specification in result
    ] == [
        "valve_type",
        "media_volume",
    ]

    assert result[0].label == "Valve Type"
    assert result[0].value_text == "Pass-Through"
    assert result[0].unit is None

    assert result[1].unit == "cu ft"


def test_public_specification_response_hides_source_reference() -> None:
    result = public_specification_reads(
        [
            make_specification(
                spec_key="gpd",
                label="Production",
                value_text="50",
                unit="GPD",
            )
        ]
    )

    payload = result[0].model_dump()

    assert "source_reference" not in payload
    assert "verified_at" not in payload

import pytest
from pydantic import ValidationError

from app.schemas.quote import (
    QuoteRequestCreate,
)


def test_quote_email_is_normalized() -> None:
    payload = QuoteRequestCreate(
        name=" Test Customer ",
        email=" PERSON@EXAMPLE.TEST ",
        message=" Interested in this system. ",
    )

    assert payload.name == "Test Customer"
    assert payload.email == "person@example.test"
    assert payload.message == "Interested in this system."


def test_quote_requires_email_shape() -> None:
    with pytest.raises(ValidationError):
        QuoteRequestCreate(
            name="Test Customer",
            email="not-an-email",
        )

def test_public_quote_response_has_no_internal_notes() -> None:
    from app.schemas.quote import QuoteRequestRead

    payload = QuoteRequestRead(
        id="quote-id",
        status="new",
    ).model_dump()

    assert payload == {
        "id": "quote-id",
        "status": "new",
    }

    assert "internal_notes" not in payload


def test_recommendation_context_is_structured_and_cleaned() -> None:
    payload = QuoteRequestCreate(
        name="Test Customer",
        email="person@example.test",
        recommendation_context={
            "source_water": "municipal",
            "hard_water_signs": "yes",
            "bathrooms": "2",
            "water_quality_report_read": "no",
            "chlorine_chloramine_signs": "unsure",
            "iron_manganese_concerns": "no",
            "existing_equipment": "  Existing softener  ",
            "drain_available": "yes",
            "electrical_available": "yes",
            "irrigation_hose_bib": "yes",
            "pool_autofill": "no",
            "drinking_water_ro": "no",
            "water_test_results": "yes",
            "water_filtration_network": "yes",
            "treatment_preference": "softened",
        },
    )

    assert payload.recommendation_context is not None
    assert payload.recommendation_context.source_water == "municipal"
    assert payload.recommendation_context.existing_equipment == "Existing softener"


def test_recommendation_context_rejects_unknown_source_water() -> None:
    with pytest.raises(ValidationError):
        QuoteRequestCreate(
            name="Test Customer",
            email="person@example.test",
            recommendation_context={
                "source_water": "spring",
                "hard_water_signs": "unsure",
                "bathrooms": "unsure",
                "water_quality_report_read": "unsure",
                "chlorine_chloramine_signs": "unsure",
                "iron_manganese_concerns": "unsure",
                "existing_equipment": None,
                "drain_available": "unsure",
                "electrical_available": "unsure",
                "irrigation_hose_bib": "unsure",
                "pool_autofill": "unsure",
                "drinking_water_ro": "unsure",
                "water_test_results": "unsure",
                "water_filtration_network": "unsure",
                "treatment_preference": "unsure",
            },
        )

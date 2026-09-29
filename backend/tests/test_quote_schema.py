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
            "service_postal_code": " 92618 ",
            "hard_water_signs": "yes",
            "water_hardness": " 12 gpg ",
            "bathrooms": "2",
            "occupants": 4,
            "water_service_pipe_size": "1 inch",
            "water_quality_report_read": "no",
            "chlorine_chloramine_signs": "unsure",
            "chlorine_chloramine_details": "  utility report available ",
            "iron_manganese_concerns": "no",
            "iron_manganese_details": None,
            "ph": 7.4,
            "existing_equipment": "  Existing softener  ",
            "drain_available": "yes",
            "electrical_available": "yes",
            "irrigation_hose_bib": "yes",
            "pool_autofill": "no",
            "drinking_water_ro": "no",
            "water_test_results": "yes",
            "water_filtration_network": "yes",
            "water_filtration_network_details": "  Neighbors use carbon filtration. ",
            "treatment_preference": "softened",
        },
    )

    assert payload.recommendation_context is not None
    assert payload.recommendation_context.source_water == "municipal"
    assert payload.recommendation_context.service_postal_code == "92618"
    assert payload.recommendation_context.water_hardness == "12 gpg"
    assert payload.recommendation_context.ph == 7.4
    assert payload.recommendation_context.water_filtration_network_details == (
        "Neighbors use carbon filtration."
    )
    assert payload.recommendation_context.existing_equipment == "Existing softener"
    assert payload.recommendation_context.occupants == 4
    assert payload.recommendation_context.water_service_pipe_size == "1 inch"


def test_recommendation_context_rejects_unknown_source_water() -> None:
    with pytest.raises(ValidationError):
        QuoteRequestCreate(
            name="Test Customer",
            email="person@example.test",
            recommendation_context={
                "source_water": "spring",
                "hard_water_signs": "unsure",
                "bathrooms": "unsure",
            "occupants": None,
            "water_service_pipe_size": None,
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


def test_recommendation_context_rejects_invalid_ph() -> None:
    with pytest.raises(ValidationError):
        QuoteRequestCreate(
            name="Test Customer",
            email="person@example.test",
            recommendation_context={
                "source_water": "municipal",
                "hard_water_signs": "unsure",
                "bathrooms": "unsure",
                "occupants": None,
                "water_service_pipe_size": None,
                "water_quality_report_read": "unsure",
                "chlorine_chloramine_signs": "unsure",
                "iron_manganese_concerns": "unsure",
                "ph": 15,
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


def test_recommendation_decision_has_stable_machine_fields() -> None:
    from app.schemas.quote import RecommendationDecision

    payload = RecommendationDecision(
        code="limited_utilities",
        title="Harmony + cartridge filtration",
        description="Starting path.",
        human_review=False,
        components=["harmony", "cartridge_filtration"],
        sizing={
            "status": "needs_more_information",
            "missing_inputs": [
                "bathrooms",
                "occupants",
                "water_service_pipe_size",
            ],
            "capacity_recommendation_available": False,
        },
    ).model_dump()

    assert payload["code"] == "limited_utilities"
    assert payload["human_review"] is False
    assert payload["requires_third_party_lab"] is False
    assert payload["components"] == [
        "harmony",
        "cartridge_filtration",
    ]

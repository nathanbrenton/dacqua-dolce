from app.schemas.quote import RecommendationContext
from app.services.recommendations import (
    RECOMMENDATION_POLICY_VERSION,
    evaluate_recommendation,
)


def context(**overrides: object) -> RecommendationContext:
    values: dict[str, object] = {
        "source_water": "municipal",
        "hard_water_signs": "unsure",
        "bathrooms": "unsure",
        "occupants": None,
        "water_service_pipe_size": None,
        "water_quality_report_read": "unsure",
        "chlorine_chloramine_signs": "unsure",
        "iron_manganese_concerns": "unsure",
        "existing_equipment": None,
        "drain_available": "yes",
        "electrical_available": "yes",
        "irrigation_hose_bib": "unsure",
        "pool_autofill": "unsure",
        "drinking_water_ro": "unsure",
        "water_test_results": "unsure",
        "water_filtration_network": "unsure",
        "treatment_preference": "unsure",
    }
    values.update(overrides)
    return RecommendationContext.model_validate(values)


def test_well_water_requires_third_party_lab_and_review() -> None:
    result = evaluate_recommendation(context(source_water="well"))

    assert result.code == "well_testing_required"
    assert result.human_review is True
    assert result.requires_third_party_lab is True
    assert result.components == []


def test_unknown_source_water_requires_review() -> None:
    result = evaluate_recommendation(context(source_water="unsure"))

    assert result.code == "source_water_review"
    assert result.human_review is True


def test_missing_power_uses_limited_utilities_path() -> None:
    result = evaluate_recommendation(context(electrical_available="no"))

    assert result.code == "limited_utilities"
    assert result.human_review is False
    assert result.components == ["harmony", "cartridge_filtration"]


def test_missing_drain_uses_limited_utilities_path() -> None:
    result = evaluate_recommendation(context(drain_available="no"))

    assert result.code == "limited_utilities"


def test_unknown_installation_utilities_require_review() -> None:
    result = evaluate_recommendation(context(drain_available="unsure"))

    assert result.code == "installation_review"
    assert result.human_review is True


def test_salt_free_path_is_authoritative() -> None:
    result = evaluate_recommendation(context(treatment_preference="salt_free"))

    assert result.code == "salt_free"
    assert result.components == ["backwashing_carbon", "harmony"]


def test_softener_path_always_includes_reverse_osmosis() -> None:
    result = evaluate_recommendation(
        context(
            treatment_preference="softened",
            drinking_water_ro="no",
        )
    )

    assert result.code == "softened_with_ro"
    assert result.components == [
        "backwashing_carbon",
        "water_softener",
        "reverse_osmosis",
    ]


def test_unknown_treatment_preference_requires_review() -> None:
    result = evaluate_recommendation(context(treatment_preference="unsure"))

    assert result.code == "treatment_preference_review"
    assert result.human_review is True


def test_sizing_readiness_reports_missing_inputs_without_guessing_capacity() -> None:
    result = evaluate_recommendation(context(treatment_preference="salt_free"))

    assert result.sizing.status == "needs_more_information"
    assert result.sizing.missing_inputs == [
        "bathrooms",
        "occupants",
        "water_service_pipe_size",
    ]
    assert result.sizing.capacity_recommendation_available is False


def test_sizing_readiness_is_complete_when_confirmed_inputs_are_present() -> None:
    result = evaluate_recommendation(
        context(
            treatment_preference="salt_free",
            bathrooms="3",
            occupants=4,
            water_service_pipe_size="1 inch",
        )
    )

    assert result.sizing.status == "inputs_complete"
    assert result.sizing.missing_inputs == []
    assert result.sizing.capacity_recommendation_available is False


def test_recommendation_policy_version_is_explicit() -> None:
    assert RECOMMENDATION_POLICY_VERSION == "2"

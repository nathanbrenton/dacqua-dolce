from app.schemas.quote import (
    RecommendationContext,
    RecommendationDecision,
    RecommendationSizingAssessment,
)

RECOMMENDATION_POLICY_VERSION = "3"


def evaluate_sizing_readiness(
    context: RecommendationContext,
) -> RecommendationSizingAssessment:
    missing_inputs = []

    if context.bathrooms == "unsure":
        missing_inputs.append("bathrooms")

    if context.occupants is None:
        missing_inputs.append("occupants")

    if context.water_service_pipe_size is None:
        missing_inputs.append("water_service_pipe_size")

    return RecommendationSizingAssessment(
        status=(
            "inputs_complete"
            if not missing_inputs
            else "needs_more_information"
        ),
        missing_inputs=missing_inputs,
        capacity_recommendation_available=False,
    )


def evaluate_recommendation(
    context: RecommendationContext,
) -> RecommendationDecision:
    sizing = evaluate_sizing_readiness(context)
    if context.source_water == "well":
        return RecommendationDecision(
            code="well_testing_required",
            title="Third-party water testing comes first.",
            description=(
                "Well-water systems require third-party laboratory testing "
                "and human review before D'Acqua Dolce makes a system recommendation."
            ),
            human_review=True,
            requires_third_party_lab=True,
            sizing=sizing,
        )

    if context.source_water != "municipal":
        return RecommendationDecision(
            code="source_water_review",
            title="Source water comes first.",
            description=(
                "Confirm whether the property uses municipal or well water before "
                "a final system recommendation is made."
            ),
            human_review=True,
            sizing=sizing,
        )

    if context.electrical_available == "no" or context.drain_available == "no":
        return RecommendationDecision(
            code="limited_utilities",
            title="Harmony + cartridge filtration",
            description=(
                "With power or a backwash drain unavailable, Harmony conditioning "
                "with cartridge filtration is the current starting path. During "
                "the assisted-sales phase, a D'Acqua Dolce employee confirms the "
                "final system fit before purchase."
            ),
            human_review=True,
            components=[
                "harmony",
                "cartridge_filtration",
            ],
            sizing=sizing,
        )

    if (
        context.electrical_available != "yes"
        or context.drain_available != "yes"
    ):
        return RecommendationDecision(
            code="installation_review",
            title="Installation review recommended.",
            description=(
                "Power and drain availability are needed before choosing between "
                "the confirmed backwashing treatment paths."
            ),
            human_review=True,
            sizing=sizing,
        )

    if context.treatment_preference == "salt_free":
        return RecommendationDecision(
            code="salt_free",
            title="Backwashing carbon + Harmony",
            description=(
                "For municipal water with power and drain access, this is the "
                "current starting path when carbon filtration and scale/deposit "
                "mitigation without salt are preferred. During the assisted-sales "
                "phase, a D'Acqua Dolce employee confirms the final system fit "
                "before purchase."
            ),
            human_review=True,
            components=[
                "backwashing_carbon",
                "harmony",
            ],
            sizing=sizing,
        )

    if context.treatment_preference == "softened":
        return RecommendationDecision(
            code="softened_with_ro",
            title="Backwashing carbon + water softener + reverse osmosis",
            description=(
                "For municipal water with power and drain access, this is the "
                "current starting path when conventionally softened water is "
                "preferred. Reverse osmosis is included with the softener path. "
                "During the assisted-sales phase, a D'Acqua Dolce employee confirms "
                "the final system fit before purchase."
            ),
            human_review=True,
            components=[
                "backwashing_carbon",
                "water_softener",
                "reverse_osmosis",
            ],
            sizing=sizing,
        )

    return RecommendationDecision(
        code="treatment_preference_review",
        title="Expert review recommended.",
        description=(
            "The confirmed starting paths depend on whether salt-free conditioning "
            "or conventionally softened water is preferred."
        ),
        human_review=True,
        sizing=sizing,
    )

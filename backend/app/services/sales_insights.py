from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class InsightBucket:
    value: str
    count: int


@dataclass(frozen=True)
class AssistedSalesInsights:
    total_requests: int
    structured_requests: int
    source_water: tuple[InsightBucket, ...]
    treatment_preference: tuple[InsightBucket, ...]
    service_postal_codes: tuple[InsightBucket, ...]
    limited_utility_requests: int
    lab_required_requests: int
    known_hardness_requests: int
    research_network_yes: int


def _buckets(counter: Counter[str], *, limit: int | None = None) -> tuple[InsightBucket, ...]:
    rows = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    if limit is not None:
        rows = rows[:limit]
    return tuple(InsightBucket(value=value, count=count) for value, count in rows)


def summarize_assisted_sales(
    rows: Iterable[tuple[dict[str, object] | None, dict[str, object] | None]],
) -> AssistedSalesInsights:
    total_requests = 0
    structured_requests = 0
    source_water: Counter[str] = Counter()
    treatment_preference: Counter[str] = Counter()
    service_postal_codes: Counter[str] = Counter()
    limited_utility_requests = 0
    lab_required_requests = 0
    known_hardness_requests = 0
    research_network_yes = 0

    for context, decision in rows:
        total_requests += 1

        if isinstance(decision, dict) and decision.get("requires_third_party_lab") is True:
            lab_required_requests += 1

        if not isinstance(context, dict):
            continue

        structured_requests += 1

        source = context.get("source_water")
        if isinstance(source, str) and source:
            source_water[source] += 1

        treatment = context.get("treatment_preference")
        if isinstance(treatment, str) and treatment:
            treatment_preference[treatment] += 1

        postal_code = context.get("service_postal_code")
        if isinstance(postal_code, str) and postal_code.strip():
            service_postal_codes[postal_code.strip()] += 1

        if context.get("electrical_available") == "no" or context.get("drain_available") == "no":
            limited_utility_requests += 1

        hardness = context.get("water_hardness")
        if isinstance(hardness, str) and hardness.strip():
            known_hardness_requests += 1

        if context.get("water_filtration_network") == "yes":
            research_network_yes += 1

    return AssistedSalesInsights(
        total_requests=total_requests,
        structured_requests=structured_requests,
        source_water=_buckets(source_water),
        treatment_preference=_buckets(treatment_preference),
        service_postal_codes=_buckets(service_postal_codes, limit=8),
        limited_utility_requests=limited_utility_requests,
        lab_required_requests=lab_required_requests,
        known_hardness_requests=known_hardness_requests,
        research_network_yes=research_network_yes,
    )

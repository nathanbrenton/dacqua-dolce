from app.services.sales_insights import summarize_assisted_sales


def test_assisted_sales_summary_keeps_research_signal_separate() -> None:
    rows = [
        (
            {
                "source_water": "municipal",
                "service_postal_code": "92618",
                "water_hardness": "12 gpg",
                "electrical_available": "yes",
                "drain_available": "yes",
                "treatment_preference": "salt_free",
                "water_filtration_network": "yes",
            },
            {"requires_third_party_lab": False},
        ),
        (
            {
                "source_water": "well",
                "service_postal_code": "92618",
                "water_hardness": None,
                "electrical_available": "no",
                "drain_available": "unsure",
                "treatment_preference": "unsure",
                "water_filtration_network": "no",
            },
            {"requires_third_party_lab": True},
        ),
        (None, None),
    ]

    summary = summarize_assisted_sales(rows)

    assert summary.total_requests == 3
    assert summary.structured_requests == 2
    assert summary.limited_utility_requests == 1
    assert summary.lab_required_requests == 1
    assert summary.known_hardness_requests == 1
    assert summary.research_network_yes == 1
    assert [(item.value, item.count) for item in summary.service_postal_codes] == [
        ("92618", 2)
    ]
    assert {(item.value, item.count) for item in summary.source_water} == {
        ("municipal", 1),
        ("well", 1),
    }


def test_assisted_sales_summary_limits_postal_code_rankings() -> None:
    rows = [
        (
            {
                "source_water": "municipal",
                "service_postal_code": f"9000{index}",
                "water_hardness": None,
                "electrical_available": "yes",
                "drain_available": "yes",
                "treatment_preference": "unsure",
                "water_filtration_network": "unsure",
            },
            None,
        )
        for index in range(10)
    ]

    summary = summarize_assisted_sales(rows)

    assert len(summary.service_postal_codes) == 8

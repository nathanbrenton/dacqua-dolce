from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def csrf() -> str:
    response = client.get("/api/auth/csrf")

    assert response.status_code == 200

    return response.json()["csrf_token"]


def base_context() -> dict[str, object]:
    return {
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
        "drinking_water_ro": "no",
        "water_test_results": "unsure",
        "water_filtration_network": "unsure",
        "treatment_preference": "softened",
    }


def test_recommendation_endpoint_returns_structured_softener_decision() -> None:
    response = client.post(
        "/api/quotes/recommendation",
        json=base_context(),
        headers={"X-CSRF-Token": csrf()},
    )

    assert response.status_code == 200
    assert response.json() == {
        "code": "softened_with_ro",
        "title": "Backwashing carbon + water softener + reverse osmosis",
        "description": (
            "For municipal water with power and drain access, this is the "
            "confirmed starting path when conventionally softened water is "
            "preferred. Reverse osmosis is always included with the softener "
            "recommendation."
        ),
        "human_review": False,
        "requires_third_party_lab": False,
        "components": [
            "backwashing_carbon",
            "water_softener",
            "reverse_osmosis",
        ],
        "sizing": {
            "status": "needs_more_information",
            "missing_inputs": [
                "bathrooms",
                "occupants",
                "water_service_pipe_size",
            ],
            "capacity_recommendation_available": False,
        },
    }


def test_recommendation_endpoint_enforces_well_water_testing_boundary() -> None:
    payload = base_context()
    payload["source_water"] = "well"

    response = client.post(
        "/api/quotes/recommendation",
        json=payload,
        headers={"X-CSRF-Token": csrf()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "well_testing_required"
    assert body["human_review"] is True
    assert body["requires_third_party_lab"] is True
    assert body["components"] == []

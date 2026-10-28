"""PT54-C3: candidate evidence must never become commercial authorization."""
from __future__ import annotations

import copy

import pytest

from app.schemas.product_configuration import CARTRIDGE_CHOICES, FITTING_CHOICES, SKU_FAMILY
from app.services.commercial_evidence_intake import (
    expected_identities,
    make_template,
    review_report,
    validate_intake,
)


def editable() -> dict:
    return make_template()


def find(data: dict, kind: str) -> dict:
    return next(item for item in data["records"] if item["kind"] == kind)


def source(item: dict) -> None:
    item["evidence"].update(
        source_type="supplier_document",
        source_reference="SUPPLIER-EXAMPLE",
        source_date="2026-10-25",
    )


def test_complete_template_is_pending_and_authorizes_nothing():
    data = editable()
    assert len(data["records"]) == 38
    assert len(expected_identities()) == 38
    assert sum(r["kind"] == "fitting" for r in data["records"]) == 20
    assert sum(r["kind"] == "pureline_cartridge" for r in data["records"]) == 14
    assert sum(r["kind"] == "harmony_2cf" for r in data["records"]) == 4
    assert len(FITTING_CHOICES) == 10
    assert sum(map(len, CARTRIDGE_CHOICES.values())) == 14
    report = review_report(data)
    assert report["commercially_authorized"] == 0
    assert report["submitted_for_staff_review"] == 0
    assert all(not row["commercially_authorized"] for row in report["records"])
    assert all(row["review_state"] == "incomplete" for row in report["records"])


def test_supplier_fitment_claim_with_provenance_is_still_unapproved():
    data = editable()
    item = find(data, "fitting")
    item["claim"].update(
        manufacturer="Example Manufacturer",
        compatibility_claim="supplier_claims_compatible",
    )
    source(item)
    report = review_report(data)
    row = next(r for r in report["records"] if r["kind"] == "fitting")
    assert row["review_state"] == "submitted_for_staff_review"
    assert row["commercially_authorized"] is False
    assert report["commercially_authorized"] == 0


def test_unproven_claim_receives_blocker_and_is_not_authorized():
    data = editable()
    item = find(data, "fitting")
    item["claim"]["compatibility_claim"] = "supplier_claims_compatible"
    report = review_report(data)
    row = next(r for r in report["records"] if r["kind"] == "fitting")
    assert any("Traceable evidence" in msg for msg in row["blockers"])
    assert not row["commercially_authorized"]


def test_pureline_model_position_price_proposals_are_not_saleable():
    data = editable()
    item = find(data, "pureline_cartridge")
    item["claim"].update(
        manufacturer_model="EXAMPLE-MODEL",
        claimed_housing_models=["EXAMPLE-HOUSING"],
        claimed_positions=[1, 3],
        supplier_cost_usd="8.55",
        proposed_selling_price_usd="29.95",
    )
    source(item)
    report = review_report(data)
    row = next(r for r in report["records"] if r["kind"] == "pureline_cartridge")
    assert row["review_state"] == "submitted_for_staff_review"
    assert not row["commercially_authorized"]


def test_harmony_skus_are_proposals_only():
    data = editable()
    item = find(data, "harmony_2cf")
    item["claim"].update(proposed_sku="PROPOSED-H20", proposed_selling_price_usd="1200.00")
    source(item)
    report = review_report(data)
    row = next(r for r in report["records"] if r["kind"] == "harmony_2cf")
    assert row["review_state"] == "submitted_for_staff_review"
    assert row["commercially_authorized"] is False
    assert "PROPOSED-H20" not in SKU_FAMILY


@pytest.mark.parametrize(
    "value", ["-1", "10.999", "1e3", "NaN", 100, "1,000", "0x10", "", " 10.00"]
)
def test_invalid_money_rejected(value):
    data = editable()
    find(data, "fitting")["claim"]["supplier_cost_usd"] = value
    with pytest.raises(ValueError):
        validate_intake(data)


@pytest.mark.parametrize("status", ["approved", "authorized", "in_stock", True])
def test_approval_status_injection_rejected(status):
    data = editable()
    find(data, "fitting")["claim"]["approval_status"] = status
    with pytest.raises(ValueError):
        validate_intake(data)


@pytest.mark.parametrize("claim", ["approved", "verified", "compatible", True])
def test_authorized_compatibility_words_rejected(claim):
    data = editable()
    find(data, "fitting")["claim"]["compatibility_claim"] = claim
    with pytest.raises(ValueError):
        validate_intake(data)


def test_missing_duplicate_and_unknown_entries_fail_closed():
    data = editable()
    data["records"].pop()
    with pytest.raises(ValueError):
        validate_intake(data)
    data = editable()
    data["records"][1] = copy.deepcopy(data["records"][0])
    with pytest.raises(ValueError):
        validate_intake(data)
    data = editable()
    data["records"][0]["identity"]["reference_order_no"] = "invented"
    with pytest.raises(ValueError):
        validate_intake(data)


def test_invalid_harmony_sku_reuse_and_duplicates_rejected():
    data = editable()
    find(data, "harmony_2cf")["claim"]["proposed_sku"] = "DD15SOFT"
    with pytest.raises(ValueError):
        validate_intake(data)
    data = editable()
    harmony = [x for x in data["records"] if x["kind"] == "harmony_2cf"]
    harmony[0]["claim"]["proposed_sku"] = "PROPOSED01"
    harmony[1]["claim"]["proposed_sku"] = "PROPOSED01"
    with pytest.raises(ValueError):
        validate_intake(data)


def test_invalid_positions_and_housing_claims_rejected():
    for positions in ([True], [0], [4], [1, 1], ["1"]):
        data = editable()
        find(data, "pureline_cartridge")["claim"]["claimed_positions"] = positions
        with pytest.raises(ValueError):
            validate_intake(data)
    data = editable()
    find(data, "fitting")["claim"]["claimed_positions"] = [1]
    with pytest.raises(ValueError):
        validate_intake(data)


@pytest.mark.parametrize("date_value", ["2026-02-30", "10/25/2026", "2026-1-1", True])
def test_bad_source_dates_rejected(date_value):
    data = editable()
    find(data, "fitting")["evidence"]["source_date"] = date_value
    with pytest.raises(ValueError):
        validate_intake(data)


def test_scope_or_schema_mutations_rejected():
    for field, value in [("purpose", "approved_catalog"), ("schema_version", True)]:
        data = editable()
        data[field] = value
        with pytest.raises(ValueError):
            validate_intake(data)

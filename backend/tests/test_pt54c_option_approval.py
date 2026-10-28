"""PT54-C approval-gate regressions: no invented supplier fitment or prices."""

import pytest

from app.schemas.product_configuration import (
    CARTRIDGE_CHOICES,
    FITTING_CHOICES,
    ProductConfigurationRequest,
)
from app.services.option_approval import (
    review_fitting,
    review_pureline_cartridge,
)
from app.services.product_configuration import configuration_inquiry_text


@pytest.mark.parametrize("valve", ["clack", "performance"])
@pytest.mark.parametrize("order_no", sorted(FITTING_CHOICES))
def test_every_reference_fitting_valve_pair_requires_review(valve: str, order_no: str) -> None:
    decision = review_fitting(valve, order_no)
    assert decision.approval_status == "unverified"
    assert decision.compatibility_confirmed is False
    assert decision.sales_price_authorized is False
    assert decision.approved_supplier_model is None
    assert decision.evidence_reference is None
    assert decision.staff_review_required is True


@pytest.mark.parametrize("valve,order_no", [
    ("unknown", "V3007-03LF"), ("clack", "V9999"), ("performance", ""),
])
def test_unknown_valves_and_parts_fail_closed(valve: str, order_no: str) -> None:
    with pytest.raises(ValueError):
        review_fitting(valve, order_no)


def test_both_valves_produce_explicit_staff_approval_hold_in_customer_inquiry() -> None:
    for valve in ("clack", "performance"):
        configuration = ProductConfigurationRequest(
            sku="DD15SOFT", tank_size_cf="1.5", finish="stainless", valve=valve,
            fitting={"order_no": "V3007-03LF", "size": '3/4"'},
        )
        text = configuration_inquiry_text(configuration)
        assert f"Fitting approval for {valve} valve: UNVERIFIED" in text
        assert "before a formal offer" in text
        assert "not a priced or approved order" in text.lower()


@pytest.mark.parametrize("category,cartridge", [
    (category, value) for category, values in CARTRIDGE_CHOICES.items() for value in sorted(values)
])
def test_named_pureline_choices_are_not_order_or_price_authorized(
    category: str, cartridge: str
) -> None:
    decision = review_pureline_cartridge(category, cartridge)
    assert decision.approval_status == "unverified"
    assert not decision.compatibility_confirmed
    assert not decision.sales_price_authorized


def test_unknown_cartridges_fail_closed_and_other_is_unpriced() -> None:
    with pytest.raises(ValueError):
        review_pureline_cartridge("carbon", "unknown carbon")
    with pytest.raises(ValueError):
        review_pureline_cartridge("unlisted", None)
    with pytest.raises(ValueError):
        review_pureline_cartridge("other", "unsupported model")
    assert review_pureline_cartridge("other", None).staff_review_required


def test_harmony_housing_reviews_are_separate_and_20_stays_quote_only() -> None:
    configuration = ProductConfigurationRequest(
        sku="DD15CLEARPL2", tank_size_cf="2.0", finish="neoprene",
        housings=[
            {"position": 2, "category": "iron", "cartridge": "Iron cartridge"},
            {"position": 1, "category": "carbon", "cartridge": 'GAC — 4" diameter'},
        ],
    )
    text = configuration_inquiry_text(configuration)
    assert "no authorized saleable SKU or price" in text
    assert text.index("Pureline housing 1 approval: UNVERIFIED") < text.index(
        "Pureline housing 2 approval: UNVERIFIED"
    )
    assert "before a formal offer" in text

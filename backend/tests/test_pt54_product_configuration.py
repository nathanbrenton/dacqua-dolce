"""PT54-A customer quote configuration contract: no sale/price authority."""

import pytest
from pydantic import ValidationError

from app.schemas.product_configuration import ProductConfigurationRequest
from app.schemas.quote import QuoteRequestCreate
from app.services.product_configuration import configuration_inquiry_text


def make(**overrides: object) -> ProductConfigurationRequest:
    fields = {
        "sku": "DD15SOFT",
        "tank_size_cf": "1.5",
        "finish": "stainless",
        "valve": "clack",
    }
    fields.update(overrides)
    return ProductConfigurationRequest.model_validate(fields)


def test_refine_reference_fitting_and_jacket_are_in_staff_note():
    request = make(
        finish="neoprene",
        valve="performance",
        fitting={"order_no": "V3007-03LF", "size": '3/4"'},
    )
    note = configuration_inquiry_text(request)
    assert "+$100" in note
    assert "NOT included in any cart amount" in note
    assert "V3007-03LF" in note
    assert "Confirm Clack-reference fitting compatibility" in note
    assert "NOT a priced or approved order" in note


def test_unknown_fitting_and_size_mismatch_rejected():
    for fitting in (
        {"order_no": "V9999", "size": '3/4"'},
        {"order_no": "V3007-03LF", "size": '1"'},
    ):
        with pytest.raises(ValidationError):
            make(fitting=fitting)


def test_125inch_fitting_must_not_be_mislabeled_shared_15inch():
    with pytest.raises(ValidationError):
        make(fitting={"order_no": "V3007-05", "size": '1.25" / 1.5"'})
    assert make(fitting={"order_no": "V3007-05", "size": '1.25"'}).fitting is not None


def test_refine_and_essence_size_must_match_catalog_sku():
    with pytest.raises(ValidationError):
        make(tank_size_cf="2.0")
    assert make(sku="DD20SOFT", tank_size_cf="2.0").sku == "DD20SOFT"
    assert make(sku="DD20CATRV", tank_size_cf="2.0").sku == "DD20CATRV"


def test_harmony_20_is_quote_only_and_position_selections_are_independent():
    config = make(
        sku="DD15CLEARPL2", tank_size_cf="2.0", valve=None,
        housings=[
            {"position": 2, "category": "sediment", "cartridge": "Sediment — 5 micron"},
            {"position": 1, "category": "carbon", "cartridge": 'GAC — 4" diameter'},
        ],
    )
    note = configuration_inquiry_text(config)
    assert "no authorized saleable SKU or price" in note
    assert note.index("Pureline housing 1") < note.index("Pureline housing 2")


def test_harmony_rejects_inexistent_or_duplicate_housing_positions():
    for choices in (
        [{"position": 3, "category": "iron", "cartridge": "Iron cartridge"}],
        [{"position": 1, "category": "iron"}, {"position": 1, "category": "carbon"}],
    ):
        with pytest.raises(ValidationError):
            make(sku="DD15CLEARPL2", tank_size_cf="1.5", valve=None, housings=choices)


def test_other_cartridge_description_is_bounded_and_not_an_inventory_sku():
    config = make(
        sku="DD15CLEARPL1", valve=None,
        housings=[{"position": 1, "category": "other", "other_description": "bone media"}],
    )
    assert "bone media" in configuration_inquiry_text(config)
    for value in ("x" * 121, "control\ncharacter"):
        with pytest.raises(ValidationError):
            make(
                sku="DD15CLEARPL1", valve=None,
                housings=[{"position": 1, "category": "other", "other_description": value}],
            )


def test_known_cartridge_option_required_if_specified():
    with pytest.raises(ValidationError):
        make(
            sku="DD15CLEARPL1", valve=None,
            housings=[{"position": 1, "category": "carbon", "cartridge": "unverified carbon"}],
        )


def test_harmony_ptv_only_cannot_request_cartridge_or_clack_fitting():
    with pytest.raises(ValidationError):
        make(sku="DD15CLEARPTV", valve=None,
             housings=[{"position": 1, "category": "sediment"}])
    with pytest.raises(ValidationError):
        make(sku="DD15CLEARPTV", valve=None,
             fitting={"order_no": "V3007-03LF", "size": '3/4"'})


def test_origin_stage_selection_no_whole_house_hardware():
    assert ProductConfigurationRequest(sku="DD6ROAE").sku == "DD6ROAE"
    with pytest.raises(ValidationError):
        make(sku="DD6ROAE", tank_size_cf="1.5")


def test_quote_schema_accepts_config_without_price_or_cart_modification():
    payload = QuoteRequestCreate(
        inquiry_context="product_inquiry",
        product_id="00000000-0000-0000-0000-000000000001",
        name="Test", email="test@example.test",
        configuration=make().model_dump(),
    )
    assert payload.configuration is not None
    assert payload.configuration.sku == "DD15SOFT"
    with pytest.raises(ValidationError):
        QuoteRequestCreate(
            name="Test", email="test@example.test",
            configuration={**make().model_dump(), "unit_price": 1},
        )

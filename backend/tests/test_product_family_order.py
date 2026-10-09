from types import SimpleNamespace
import pytest
from app.services.product_family_order import available_families, complete_order, sort_products, stored_order


def product(name, family=None):
    return SimpleNamespace(name=name, product_family=family, id=name)


def test_default_order_and_unknown_family_fallback():
    products = [product("Harmony"), product("Other"), product("Origin"), product("Refine")]
    order = complete_order(available_families(products), stored_order(None))
    assert [p.name for p in sort_products(products, order)] == ["Refine", "Harmony", "Origin", "Other"]


def test_variants_are_grouped_and_alphabetical_within_family():
    products = [product("Refine Z", "Refine"), product("Essence"), product("Refine A", "Refine")]
    result = sort_products(products, ["Refine", "Essence"])
    assert [p.name for p in result] == ["Refine A", "Refine Z", "Essence"]


def test_duplicate_stored_families_are_normalized():
    assert complete_order(["A", "B"], ["B", "B"]) == ["B", "A"]


def test_invalid_stored_payload_fails_closed():
    with pytest.raises(ValueError):
        stored_order('{"not":"an array"}')

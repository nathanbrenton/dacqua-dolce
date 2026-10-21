from types import SimpleNamespace

import pytest

from app.cli.pt41_catalog_rollout import LEGACY_SLUGS, retire_legacy_products
from app.models.catalog import ProductLifecycleStatus


class FakeDB:
    def __init__(self, products):
        self.products = products

    def scalars(self, _query):
        return SimpleNamespace(all=lambda: self.products)


def example_product(sku="REFINE", **kwargs):
    return SimpleNamespace(
        sku=sku,
        slug=kwargs.get("slug", LEGACY_SLUGS[sku]),
        active=kwargs.get("active", True),
        online_sale_approved=kwargs.get("online_sale_approved", False),
        lifecycle_status=kwargs.get("lifecycle_status", ProductLifecycleStatus.active),
    )


def test_legacy_products_retired_without_changing_identifiers():
    product = example_product()
    changes = retire_legacy_products(FakeDB([product]))
    assert changes == ["REFINE"]
    assert product.sku == "REFINE"
    assert product.slug == "refine"
    assert product.active is False
    assert product.lifecycle_status == ProductLifecycleStatus.discontinued
    assert retire_legacy_products(FakeDB([product])) == []


def test_retirement_rejects_online_sale_approval():
    with pytest.raises(RuntimeError, match="approved for online sales"):
        retire_legacy_products(FakeDB([example_product(online_sale_approved=True)]))


def test_retirement_rejects_mismatched_identity():
    with pytest.raises(RuntimeError, match="mismatch"):
        retire_legacy_products(FakeDB([example_product(slug="wrong")]))

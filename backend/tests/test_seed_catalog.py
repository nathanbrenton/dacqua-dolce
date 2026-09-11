from uuid import uuid4

from app.models.catalog import (
    Product,
    ProductSpecification,
)
from app.services.catalog_seed import (
    reconcile_product_metadata,
    reconcile_specification_metadata,
)


def test_reconcile_existing_product_updates_catalog_metadata() -> None:
    original_manufacturer_id = uuid4()
    original_category_id = uuid4()

    product = Product(
        manufacturer_id=original_manufacturer_id,
        category_id=original_category_id,
        name="Old Product Name",
        slug="dd5ro",
        sku="DD5RO",
        description="Old description.",
        product_family="Old Family",
        active=False,
        public_path="/systems/dd5ro",
    )

    new_manufacturer_id = uuid4()
    new_category_id = uuid4()

    changed = reconcile_product_metadata(
        product,
        manufacturer_id=new_manufacturer_id,
        category_id=new_category_id,
        name="Origin",
        description="Updated description.",
        product_family="Reverse Osmosis",
        public_path="/systems/dd5ro",
    )

    assert changed is True

    assert product.manufacturer_id == new_manufacturer_id
    assert product.category_id == new_category_id
    assert product.name == "Origin"
    assert product.description == "Updated description."
    assert product.product_family == "Reverse Osmosis"
    assert product.public_path == "/systems/dd5ro"

    # Stable identifiers are not rewritten by metadata reconciliation.
    assert product.sku == "DD5RO"
    assert product.slug == "dd5ro"

    # Operational state is not controlled by the catalog seed.
    assert product.active is False

def test_reconcile_specification_metadata_preserves_lifecycle_state() -> None:
    specification = ProductSpecification(
        spec_key="media_volume",
        label="Old Label",
        value_text="Old Value",
        unit=None,
        source_reference="old-source",
        public=False,
        sort_order=99,
        active=False,
        verified_at=None,
    )

    changed = reconcile_specification_metadata(
        specification,
        label="Media Volume",
        value_text="1.5",
        unit="cu ft",
        source_reference="owner-supplied SKU sheet: DD15CATPTV",
        public=True,
        sort_order=10,
    )

    assert changed is True
    assert specification.label == "Media Volume"
    assert specification.value_text == "1.5"
    assert specification.unit == "cu ft"
    assert specification.source_reference == (
        "owner-supplied SKU sheet: DD15CATPTV"
    )
    assert specification.public is True
    assert specification.sort_order == 10

    # Seed reconciliation must not silently reactivate or verify a record.
    assert specification.active is False
    assert specification.verified_at is None


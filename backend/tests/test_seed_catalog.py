import json
from uuid import uuid4

import pytest

from app.models.catalog import (
    Product,
    ProductImage,
    ProductSpecification,
)
from app.services.catalog_seed import (
    DEFAULT_CATALOG_PATH,
    CatalogSeedError,
    load_catalog_manifest,
    reconcile_image_metadata,
    reconcile_product_metadata,
    reconcile_specification_metadata,
    validate_catalog_manifest,
)


def test_production_catalog_manifest_is_valid() -> None:
    catalog = load_catalog_manifest(DEFAULT_CATALOG_PATH)
    assert catalog["schema_version"] == 1
    assert len(catalog["manufacturers"]) == 1
    assert len(catalog["categories"]) == 2
    assert len(catalog["products"]) == 10
    assert len(catalog["variants"]) == 0
    assert all(row["online_sale_approved"] is False for row in catalog["products"])

    products = {row["sku"]: row for row in catalog["products"]}
    assert set(products) == {
        "DD15SOFT", "DD20SOFT", "DD15CATRV", "DD20CATRV",
        "DD15CLEARPL1", "DD15CLEARPL2", "DD15CLEARPL3",
        "DD15CLEARPTV", "DD5RO", "DD6ROAE",
    }
    assert {p["product_family"] for p in products.values()} == {
        "Refine", "Essence", "Harmony", "Origin",
    }
    assert all(p["active"] is True for p in products.values())
    assert all(p["assisted_sale_required"] is (p["category_slug"] == "whole-home-filtration")
               for p in products.values())
    assert products["DD6ROAE"]["name"] == "Origin - Six Stage with Alkaline Enhancer"
    assert products["DD15CLEARPTV"]["name"] == "Harmony - Pass-Through Valve"
    # PT41 product copy: point-of-use terminology is authoritative for both Origin SKUs.
    assert {products[sku]["product_family"] for sku in ("DD5RO", "DD6ROAE")} == {"Origin"}
    assert all("point-of-use" in products[sku]["description"].lower()
               for sku in ("DD5RO", "DD6ROAE"))
    assert all("under-sink" not in products[sku]["description"].lower()
               for sku in ("DD5RO", "DD6ROAE"))

    specifications = {(s["product_sku"], s["spec_key"]): s["value_text"]
                      for s in catalog["specifications"]}
    assert specifications[("DD5RO", "stage_count")] == "5"
    assert specifications[("DD6ROAE", "stage_count")] == "6"
    assert specifications[("DD15CLEARPL1", "cartridge_count")] == "1"
    assert specifications[("DD15CLEARPL2", "cartridge_count")] == "2"
    assert specifications[("DD15CLEARPL3", "cartridge_count")] == "3"
    assert specifications[("DD15CLEARPTV", "cartridge_count")] == "0"
    assert all(row["product_sku"] in {"DD15CATRV", "DD5RO", "DD6ROAE"}
               for row in catalog["images"])
    assert [image["storage_path"] for image in catalog["images"]
            if image["product_sku"] == "DD6ROAE"] == [
        "/products/media/reverse-osmosis-with-remineralizer-dimensions.webp"
    ]



def test_manifest_rejects_unknown_product_reference() -> None:
    catalog = load_catalog_manifest(DEFAULT_CATALOG_PATH)
    broken = json.loads(json.dumps(catalog))
    broken["images"][0]["product_sku"] = "NOT-A-PRODUCT"

    with pytest.raises(
        CatalogSeedError,
        match="Image references unknown product",
    ):
        validate_catalog_manifest(broken)


def test_manifest_rejects_duplicate_product_sku() -> None:
    catalog = load_catalog_manifest(DEFAULT_CATALOG_PATH)
    broken = json.loads(json.dumps(catalog))
    broken["products"][1]["sku"] = broken["products"][0]["sku"]

    with pytest.raises(
        CatalogSeedError,
        match="duplicate product sku",
    ):
        validate_catalog_manifest(broken)


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
        system_type="Old System Type",
        assisted_sale_required=True,
        active=False,
        online_sale_approved=True,
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
        system_type="Reverse Osmosis System",
        assisted_sale_required=False,
        public_path="/systems/dd5ro",
    )

    assert changed is True

    assert product.manufacturer_id == new_manufacturer_id
    assert product.category_id == new_category_id
    assert product.name == "Origin"
    assert product.description == "Updated description."
    assert product.product_family == "Reverse Osmosis"
    assert product.system_type == "Reverse Osmosis System"
    assert product.assisted_sale_required is False
    assert product.public_path == "/systems/dd5ro"

    # Stable identifiers are not rewritten by metadata reconciliation.
    assert product.sku == "DD5RO"
    assert product.slug == "dd5ro"

    # Operational state is not controlled by the catalog seed.
    assert product.active is False
    assert product.online_sale_approved is True


def test_reconcile_image_metadata_preserves_lifecycle_state() -> None:
    image = ProductImage(
        storage_path="/products/media/example.webp",
        alt_text="Old alt text",
        sort_order=99,
        active=False,
    )

    changed = reconcile_image_metadata(
        image,
        alt_text="Updated alt text",
        sort_order=10,
    )

    assert changed is True
    assert image.alt_text == "Updated alt text"
    assert image.sort_order == 10
    assert image.active is False


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

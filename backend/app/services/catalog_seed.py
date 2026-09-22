from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import (
    Manufacturer,
    Product,
    ProductCategory,
    ProductImage,
    ProductSpecification,
)

DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "production_catalog.json"
)


class CatalogSeedError(RuntimeError):
    """Raised when the canonical catalog cannot be reconciled safely."""


@dataclass
class CatalogSeedResult:
    manufacturers_created: int = 0
    manufacturers_updated: int = 0
    categories_created: int = 0
    categories_updated: int = 0
    products_created: int = 0
    products_updated: int = 0
    images_created: int = 0
    images_updated: int = 0
    specifications_created: int = 0
    specifications_updated: int = 0

    @property
    def total_changes(self) -> int:
        return sum(self.__dict__.values())


def _require_unique(
    rows: list[dict[str, Any]],
    *,
    key: str,
    label: str,
) -> None:
    values = [row[key] for row in rows]

    if len(values) != len(set(values)):
        raise CatalogSeedError(
            f"Canonical catalog contains duplicate {label} {key} values."
        )


def validate_catalog_manifest(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise CatalogSeedError("Unsupported catalog schema_version.")

    required_sections = (
        "manufacturers",
        "categories",
        "products",
        "images",
        "specifications",
    )

    for section in required_sections:
        if not isinstance(data.get(section), list):
            raise CatalogSeedError(
                f"Canonical catalog section must be a list: {section}"
            )

    _require_unique(
        data["manufacturers"],
        key="slug",
        label="manufacturer",
    )
    _require_unique(
        data["categories"],
        key="slug",
        label="category",
    )
    _require_unique(
        data["products"],
        key="sku",
        label="product",
    )
    _require_unique(
        data["products"],
        key="slug",
        label="product",
    )

    manufacturer_slugs = {
        row["slug"]
        for row in data["manufacturers"]
    }
    category_slugs = {
        row["slug"]
        for row in data["categories"]
    }
    product_skus = {
        row["sku"]
        for row in data["products"]
    }

    for product in data["products"]:
        if product["manufacturer_slug"] not in manufacturer_slugs:
            raise CatalogSeedError(
                "Product references unknown manufacturer: "
                f"{product['sku']}"
            )

        if product["category_slug"] not in category_slugs:
            raise CatalogSeedError(
                "Product references unknown category: "
                f"{product['sku']}"
            )

    image_keys: set[tuple[str, str]] = set()

    for image in data["images"]:
        sku = image["product_sku"]

        if sku not in product_skus:
            raise CatalogSeedError(
                f"Image references unknown product: {sku}"
            )

        key = (sku, image["storage_path"])

        if key in image_keys:
            raise CatalogSeedError(
                "Canonical catalog contains duplicate image path for "
                f"{sku}: {image['storage_path']}"
            )

        image_keys.add(key)

    specification_keys: set[tuple[str, str]] = set()

    for specification in data["specifications"]:
        sku = specification["product_sku"]

        if sku not in product_skus:
            raise CatalogSeedError(
                f"Specification references unknown product: {sku}"
            )

        key = (sku, specification["spec_key"])

        if key in specification_keys:
            raise CatalogSeedError(
                "Canonical catalog contains duplicate specification key for "
                f"{sku}: {specification['spec_key']}"
            )

        specification_keys.add(key)


def load_catalog_manifest(
    path: Path = DEFAULT_CATALOG_PATH,
) -> dict[str, Any]:
    data = json.loads(path.read_text())
    validate_catalog_manifest(data)
    return data


def reconcile_manufacturer_metadata(
    manufacturer: Manufacturer,
    *,
    name: str,
    public_summary: str | None,
    internal_policy_notes: str | None,
) -> bool:
    desired_values = {
        "name": name,
        "public_summary": public_summary,
        "internal_policy_notes": internal_policy_notes,
    }
    return _reconcile_attributes(manufacturer, desired_values)


def reconcile_category_metadata(
    category: ProductCategory,
    *,
    name: str,
    description: str | None,
    sort_order: int,
) -> bool:
    desired_values = {
        "name": name,
        "description": description,
        "sort_order": sort_order,
    }
    return _reconcile_attributes(category, desired_values)


def reconcile_product_metadata(
    product: Product,
    *,
    manufacturer_id: UUID,
    category_id: UUID,
    name: str,
    description: str,
    product_family: str,
    public_path: str,
) -> bool:
    """Update seed-owned mutable catalog metadata on an existing product."""

    desired_values = {
        "manufacturer_id": manufacturer_id,
        "category_id": category_id,
        "name": name,
        "description": description,
        "product_family": product_family,
        "public_path": public_path,
    }

    return _reconcile_attributes(product, desired_values)


def reconcile_image_metadata(
    image: ProductImage,
    *,
    alt_text: str,
    sort_order: int,
) -> bool:
    desired_values = {
        "alt_text": alt_text,
        "sort_order": sort_order,
    }
    return _reconcile_attributes(image, desired_values)


def reconcile_specification_metadata(
    specification: ProductSpecification,
    *,
    label: str,
    value_text: str,
    unit: str | None,
    source_reference: str,
    public: bool,
    sort_order: int,
) -> bool:
    """Update seed-owned specification metadata without changing lifecycle state."""

    desired_values = {
        "label": label,
        "value_text": value_text,
        "unit": unit,
        "source_reference": source_reference,
        "public": public,
        "sort_order": sort_order,
    }

    return _reconcile_attributes(specification, desired_values)


def _reconcile_attributes(
    instance: object,
    desired_values: dict[str, object],
) -> bool:
    changed = False

    for attribute, desired_value in desired_values.items():
        if getattr(instance, attribute) == desired_value:
            continue

        setattr(instance, attribute, desired_value)
        changed = True

    return changed


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None

    return datetime.fromisoformat(value)


def _one_or_none(
    rows: list[Any],
    *,
    description: str,
) -> Any | None:
    if len(rows) > 1:
        raise CatalogSeedError(
            f"Database contains duplicate rows for {description}."
        )

    return rows[0] if rows else None


def apply_catalog_manifest(
    db: Session,
    data: dict[str, Any],
) -> CatalogSeedResult:
    validate_catalog_manifest(data)
    result = CatalogSeedResult()

    manufacturers: dict[str, Manufacturer] = {}

    for row in data["manufacturers"]:
        manufacturer = db.scalar(
            select(Manufacturer).where(
                Manufacturer.slug == row["slug"]
            )
        )

        if manufacturer is None:
            manufacturer = Manufacturer(
                name=row["name"],
                slug=row["slug"],
                public_summary=row["public_summary"],
                internal_policy_notes=row["internal_policy_notes"],
                active=row["active"],
            )
            db.add(manufacturer)
            db.flush()
            result.manufacturers_created += 1
        elif reconcile_manufacturer_metadata(
            manufacturer,
            name=row["name"],
            public_summary=row["public_summary"],
            internal_policy_notes=row["internal_policy_notes"],
        ):
            result.manufacturers_updated += 1

        manufacturers[row["slug"]] = manufacturer

    categories: dict[str, ProductCategory] = {}

    for row in data["categories"]:
        category = db.scalar(
            select(ProductCategory).where(
                ProductCategory.slug == row["slug"]
            )
        )

        if category is None:
            category = ProductCategory(
                name=row["name"],
                slug=row["slug"],
                description=row["description"],
                active=row["active"],
                sort_order=row["sort_order"],
            )
            db.add(category)
            db.flush()
            result.categories_created += 1
        elif reconcile_category_metadata(
            category,
            name=row["name"],
            description=row["description"],
            sort_order=row["sort_order"],
        ):
            result.categories_updated += 1

        categories[row["slug"]] = category

    products: dict[str, Product] = {}

    for row in data["products"]:
        product = db.scalar(
            select(Product).where(
                Product.sku == row["sku"]
            )
        )

        if product is None:
            conflicting_slug = db.scalar(
                select(Product).where(
                    Product.slug == row["slug"]
                )
            )

            if conflicting_slug is not None:
                raise CatalogSeedError(
                    "Product slug already belongs to a different SKU: "
                    f"{row['slug']}"
                )

            product = Product(
                manufacturer_id=(
                    manufacturers[row["manufacturer_slug"]].id
                ),
                category_id=categories[row["category_slug"]].id,
                name=row["name"],
                slug=row["slug"],
                sku=row["sku"],
                description=row["description"],
                product_family=row["product_family"],
                online_sale_approved=row["online_sale_approved"],
                active=row["active"],
                public_path=row["public_path"],
            )
            db.add(product)
            db.flush()
            result.products_created += 1
        else:
            if product.slug != row["slug"]:
                raise CatalogSeedError(
                    "Existing product SKU has an unexpected slug: "
                    f"{row['sku']} -> {product.slug!r}"
                )

            if reconcile_product_metadata(
                product,
                manufacturer_id=(
                    manufacturers[row["manufacturer_slug"]].id
                ),
                category_id=categories[row["category_slug"]].id,
                name=row["name"],
                description=row["description"],
                product_family=row["product_family"],
                public_path=row["public_path"],
            ):
                result.products_updated += 1

        products[row["sku"]] = product

    for row in data["images"]:
        product = products[row["product_sku"]]
        matches = db.scalars(
            select(ProductImage).where(
                ProductImage.product_id == product.id,
                ProductImage.storage_path == row["storage_path"],
            )
        ).all()
        image = _one_or_none(
            matches,
            description=(
                f"image {row['product_sku']} {row['storage_path']}"
            ),
        )

        if image is None:
            image = ProductImage(
                product_id=product.id,
                storage_path=row["storage_path"],
                alt_text=row["alt_text"],
                sort_order=row["sort_order"],
                active=row["active"],
            )
            db.add(image)
            result.images_created += 1
        elif reconcile_image_metadata(
            image,
            alt_text=row["alt_text"],
            sort_order=row["sort_order"],
        ):
            result.images_updated += 1

    for row in data["specifications"]:
        product = products[row["product_sku"]]
        specification = db.scalar(
            select(ProductSpecification).where(
                ProductSpecification.product_id == product.id,
                ProductSpecification.spec_key == row["spec_key"],
            )
        )

        if specification is None:
            specification = ProductSpecification(
                product_id=product.id,
                spec_key=row["spec_key"],
                label=row["label"],
                value_text=row["value_text"],
                unit=row["unit"],
                source_reference=row["source_reference"],
                public=row["public"],
                sort_order=row["sort_order"],
                active=row["active"],
                verified_at=_parse_datetime(row["verified_at"]),
            )
            db.add(specification)
            result.specifications_created += 1
        elif reconcile_specification_metadata(
            specification,
            label=row["label"],
            value_text=row["value_text"],
            unit=row["unit"],
            source_reference=row["source_reference"],
            public=row["public"],
            sort_order=row["sort_order"],
        ):
            result.specifications_updated += 1

    return result

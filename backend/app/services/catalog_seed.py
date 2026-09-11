from uuid import UUID

from app.models.catalog import (
    Product,
    ProductSpecification,
)


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

    changed = False

    for attribute, desired_value in desired_values.items():
        if getattr(product, attribute) == desired_value:
            continue

        setattr(product, attribute, desired_value)
        changed = True

    return changed

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

    changed = False

    for attribute, desired_value in desired_values.items():
        if getattr(specification, attribute) == desired_value:
            continue

        setattr(specification, attribute, desired_value)
        changed = True

    return changed


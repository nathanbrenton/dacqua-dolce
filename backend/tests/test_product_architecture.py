from uuid import uuid4

from app.models.catalog import (
    Product,
    ProductRelationship,
    ProductRelationshipType,
    ProductVariant,
)


def test_product_architecture_can_represent_confirmed_hierarchy() -> None:
    product = Product(
        manufacturer_id=uuid4(),
        category_id=uuid4(),
        name="Harmony",
        slug="harmony",
        sku="HARMONY",
        description="Water conditioner.",
        product_family="Harmony",
        system_type="Water Conditioner",
        online_sale_approved=False,
        active=True,
        public_path="/systems/harmony",
    )
    product.variants.append(
        ProductVariant(
            display_name="1.5 cu. ft.",
            sku="HARMONY-15",
            option_values={"capacity": "1.5 cu. ft."},
        )
    )

    uv = Product(
        manufacturer_id=uuid4(),
        category_id=uuid4(),
        name="UV option",
        slug="uv-option",
        sku="UV-OPTION",
        description="Example option record.",
        product_family=None,
        system_type=None,
        online_sale_approved=False,
        active=True,
        public_path="/systems/uv-option",
    )
    relationship = ProductRelationship(
        related_product=uv,
        relationship_type=ProductRelationshipType.option,
        public=False,
        active=True,
        sort_order=10,
    )
    product.related_options.append(relationship)

    assert product.product_family == "Harmony"
    assert product.system_type == "Water Conditioner"
    assert product.variants[0].option_values["capacity"] == "1.5 cu. ft."
    assert product.related_options[0].related_product is uv
    assert product.related_options[0].public is False

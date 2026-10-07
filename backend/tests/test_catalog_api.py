from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.catalog import catalog_product_identity_read
from app.main import app

client = TestClient(app)


def test_catalog_products_endpoint() -> None:
    response = client.get("/api/catalog/products")

    assert response.status_code == 200

    payload = response.json()

    assert "products" in payload
    assert isinstance(payload["products"], list)


def test_catalog_identity_uses_category_family_and_named_variant() -> None:
    product = SimpleNamespace(
        name="Essence - Automatic Rinse",
        product_family="Essence",
        system_type="Whole-House Carbon Filtration",
        category=SimpleNamespace(name="Whole-Home Filtration"),
    )

    identity = catalog_product_identity_read(product)  # type: ignore[arg-type]

    assert identity.category == "Whole-Home Filtration"
    assert identity.family == "Essence"
    assert identity.variant == "Automatic Rinse"


def test_catalog_identity_falls_back_to_system_type_for_family_product() -> None:
    product = SimpleNamespace(
        name="Refine",
        product_family="Refine",
        system_type="Water Softener",
        category=SimpleNamespace(name="Whole-Home Filtration"),
    )

    identity = catalog_product_identity_read(product)  # type: ignore[arg-type]

    assert identity.category == "Whole-Home Filtration"
    assert identity.family == "Refine"
    assert identity.variant == "Water Softener"

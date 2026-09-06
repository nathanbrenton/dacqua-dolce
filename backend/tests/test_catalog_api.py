from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_catalog_products_endpoint() -> None:
    response = client.get("/api/catalog/products")

    assert response.status_code == 200

    payload = response.json()

    assert "products" in payload
    assert isinstance(payload["products"], list)

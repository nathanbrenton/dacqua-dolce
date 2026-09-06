from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_product_returns_404() -> None:
    response = client.get("/api/catalog/products/definitely-not-a-real-system")

    assert response.status_code == 404
    assert response.json() == {"detail": "System not found."}

import os

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/reviews")

from app.main import app  # noqa: E402


client = TestClient(app)


def test_create_product_and_ingest_and_process():
    create_response = client.post(
        "/api/v1/products",
        json={"name": "Test Product", "source": "mock", "url": None, "external_id": None},
    )
    assert create_response.status_code == 200
    product = create_response.json()
    product_id = product["id"]

    ingest_response = client.post(f"/api/v1/products/{product_id}/ingest")
    assert ingest_response.status_code == 200
    ingest_body = ingest_response.json()
    assert ingest_body["status"] == "ok"
    assert ingest_body["ingested_reviews"] > 0

    process_response = client.post(f"/api/v1/products/{product_id}/process")
    assert process_response.status_code == 200
    process_body = process_response.json()
    assert process_body["status"] == "ok"
    assert process_body["processed_reviews"] > 0


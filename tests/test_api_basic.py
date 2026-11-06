"""API tests. Need a Postgres DATABASE_URL; LLM, embeddings and Qdrant run offline (stub / hash / in-memory)."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/reviews")
os.environ.setdefault("QDRANT_URL", ":memory:")
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("EMBED_PROVIDER", "hash")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_create_ingest_process_and_query(client):
    create_response = client.post(
        "/api/v1/products/",
        json={"name": "Test Product", "source": "mock", "url": None, "external_id": None},
    )
    assert create_response.status_code == 200
    product_id = create_response.json()["id"]

    ingest_response = client.post(f"/api/v1/products/{product_id}/ingest")
    assert ingest_response.status_code == 200
    assert ingest_response.json()["ingested_reviews"] > 0

    process_response = client.post(f"/api/v1/products/{product_id}/process")
    assert process_response.status_code == 200
    assert process_response.json()["processed_reviews"] > 0

    # Re-processing must not duplicate summaries (unique constraint) or vectors.
    assert client.post(f"/api/v1/products/{product_id}/process").status_code == 200

    assert client.get(f"/api/v1/analytics/products/{product_id}/summary").status_code == 200
    assert client.get(f"/api/v1/analytics/products/{product_id}/aspects").status_code == 200

    search = client.post(f"/api/v1/rag/products/{product_id}/semantic-search", json={"query": "battery", "top_k": 3})
    assert search.status_code == 200
    assert len(search.json()["hits"]) == 3

    qa = client.post(f"/api/v1/rag/products/{product_id}/qa", json={"question": "Is it durable?"})
    assert qa.status_code == 200
    assert qa.json()["sources"]


def test_validation(client):
    assert client.post("/api/v1/rag/products/1/qa", json={"question": ""}).status_code == 422

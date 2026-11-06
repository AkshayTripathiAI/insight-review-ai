from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import get_settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_url == ":memory:":
        return QdrantClient(location=":memory:")
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def ensure_review_collection(vector_dim: int) -> None:
    """Create the review collection, recreating it if the vector size changed (e.g. new embedding model)."""
    settings = get_settings()
    client = get_qdrant_client()
    name = settings.qdrant_collection
    vectors_config = qmodels.VectorParams(size=vector_dim, distance=qmodels.Distance.COSINE)
    if client.collection_exists(name):
        info = client.get_collection(name)
        current = info.config.params.vectors
        if getattr(current, "size", vector_dim) == vector_dim:
            return
        client.delete_collection(name)
    client.create_collection(collection_name=name, vectors_config=vectors_config)
    client.create_payload_index(name, field_name="product_id", field_schema=qmodels.PayloadSchemaType.INTEGER)


def collection_point_count() -> int:
    settings = get_settings()
    try:
        return get_qdrant_client().count(settings.qdrant_collection).count
    except Exception:
        return 0

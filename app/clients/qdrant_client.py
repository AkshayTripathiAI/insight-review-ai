from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import get_settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return client


def ensure_review_collection(vector_dim: int = 64) -> None:
    client = get_qdrant_client()
    name = "review_embeddings"
    vectors_config = qmodels.VectorParams(size=vector_dim, distance=qmodels.Distance.COSINE)
    try:
        client.get_collection(name)
    except Exception:
        client.recreate_collection(collection_name=name, vectors_config=vectors_config)

import hashlib
import math
from typing import List

import requests

from app.config import get_settings

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _hash_to_vector(text: str, dim: int) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(dim):
        byte = digest[i % len(digest)]
        value = (byte / 255.0) * 2.0 - 1.0
        values.append(value)
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


class EmbeddingService:
    """Deterministic, non-semantic vectors. Only for offline tests and local development."""

    model_name = "hash"

    def __init__(self, vector_dim: int = 64) -> None:
        self.vector_dim = vector_dim

    def embed(self, text: str, is_query: bool = False) -> List[float]:
        return _hash_to_vector(text, self.vector_dim)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


class GeminiEmbeddingService(EmbeddingService):
    """Semantic embeddings from the Gemini API (REST, no SDK needed)."""

    def __init__(self, api_key: str, model: str, vector_dim: int) -> None:
        super().__init__(vector_dim)
        self.api_key = api_key
        self.model_name = model if model.startswith("models/") else f"models/{model}"

    def _request(self, text: str, task_type: str) -> dict:
        return {
            "model": self.model_name,
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
            "outputDimensionality": self.vector_dim,
        }

    @staticmethod
    def _normalize(vector: List[float]) -> List[float]:
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed(self, text: str, is_query: bool = False) -> List[float]:
        task = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
        response = requests.post(
            f"{GEMINI_BASE}/{self.model_name}:embedContent",
            headers={"x-goog-api-key": self.api_key},
            json=self._request(text, task),
            timeout=30,
        )
        response.raise_for_status()
        return self._normalize(response.json()["embedding"]["values"])

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for start in range(0, len(texts), 100):  # API limit: 100 requests per batch
            chunk = texts[start:start + 100]
            response = requests.post(
                f"{GEMINI_BASE}/{self.model_name}:batchEmbedContents",
                headers={"x-goog-api-key": self.api_key},
                json={"requests": [self._request(t, "RETRIEVAL_DOCUMENT") for t in chunk]},
                timeout=60,
            )
            response.raise_for_status()
            vectors.extend(self._normalize(e["values"]) for e in response.json()["embeddings"])
        return vectors


def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    if settings.embed_provider == "gemini":
        if not settings.google_api_key:
            raise RuntimeError("EMBED_PROVIDER=gemini requires GOOGLE_API_KEY")
        return GeminiEmbeddingService(settings.google_api_key, settings.embed_model, settings.embed_dim)
    return EmbeddingService(vector_dim=settings.embed_dim)

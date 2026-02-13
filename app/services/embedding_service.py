import hashlib
import math
from typing import List


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
    def __init__(self, vector_dim: int = 64) -> None:
        self.vector_dim = vector_dim

    def embed(self, text: str) -> List[float]:
        return _hash_to_vector(text, self.vector_dim)


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


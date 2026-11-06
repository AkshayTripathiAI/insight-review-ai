import os
from functools import lru_cache

from pydantic import BaseModel


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/reviews")
    # Use ":memory:" for an in-process index (rebuilt from Postgres on startup).
    qdrant_url: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY") or None
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "review_embeddings")
    api_prefix: str = "/api/v1"
    project_name: str = "InsightReview AI"

    # LLM: "openai" = any OpenAI-compatible API (Groq, OpenAI, Ollama's /v1, ...),
    # "ollama-llama" = native Ollama API, "stub" = offline placeholder for tests.
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    llm_api_key: str | None = os.getenv("LLM_API_KEY") or None

    # Embeddings: "gemini" = Gemini embedding API, "hash" = deterministic offline vectors for tests.
    embed_provider: str = os.getenv("EMBED_PROVIDER", "hash")
    embed_model: str = os.getenv("EMBED_MODEL", "gemini-embedding-001")
    embed_dim: int = int(os.getenv("EMBED_DIM", "768"))
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY") or None

    # Hosted demo
    auto_bootstrap: bool = _bool("AUTO_BOOTSTRAP", False)
    demo_read_only: bool = _bool("DEMO_READ_ONLY", False)
    enable_scraping: bool = _bool("ENABLE_SCRAPING", True)
    qa_rate_limit_per_hour: int = int(os.getenv("QA_RATE_LIMIT_PER_HOUR", "60"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

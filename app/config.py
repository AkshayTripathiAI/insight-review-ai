import os
from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/reviews")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    api_prefix: str = "/api/v1"
    project_name: str = "InsightReview AI"
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.2")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    embed_model: str = os.getenv("EMBED_MODEL", "stub")


def get_settings() -> Settings:
    return Settings()

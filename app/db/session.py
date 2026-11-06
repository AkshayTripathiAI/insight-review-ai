from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


settings = get_settings()

def _normalize_url(url: str) -> str:
    """Accept plain postgres:// URLs (Neon, Render, Heroku style) and use the psycopg2 driver."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


# pool_pre_ping: serverless Postgres (e.g. Neon) closes idle connections.
engine = create_engine(_normalize_url(settings.database_url), future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


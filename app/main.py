import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import bootstrap
from app.api.routes import analytics
from app.api.routes import products
from app.api.routes import rag
from app.api.routes import reviews
from app.clients.qdrant_client import ensure_review_collection
from app.config import get_settings
from app.db import models
from app.db.session import engine

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    models.Base.metadata.create_all(bind=engine)
    ensure_review_collection(vector_dim=settings.embed_dim)
    if settings.auto_bootstrap:
        # Background thread so the server binds its port (and passes health checks) right away.
        bootstrap.start_in_background()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.project_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(products.router, prefix=settings.api_prefix + "/products", tags=["products"])
    app.include_router(reviews.router, prefix=settings.api_prefix + "/reviews", tags=["reviews"])
    app.include_router(analytics.router, prefix=settings.api_prefix + "/analytics", tags=["analytics"])
    app.include_router(rag.router, prefix=settings.api_prefix + "/rag", tags=["rag"])

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {
            "status": "ok",
            "bootstrap": bootstrap.state["status"],
            "llm": settings.llm_provider,
            "embeddings": settings.embed_provider,
        }

    return app


app = create_app()

from fastapi import FastAPI

from app.api.routes import analytics
from app.api.routes import products
from app.api.routes import rag
from app.api.routes import reviews
from app.clients.qdrant_client import ensure_review_collection
from app.config import get_settings
from app.db import models
from app.db.session import engine


def create_app() -> FastAPI:
    settings = get_settings()
    models.Base.metadata.create_all(bind=engine)
    ensure_review_collection(vector_dim=64)
    app = FastAPI(title=settings.project_name)
    app.include_router(products.router, prefix=settings.api_prefix + "/products", tags=["products"])
    app.include_router(reviews.router, prefix=settings.api_prefix + "/reviews", tags=["reviews"])
    app.include_router(analytics.router, prefix=settings.api_prefix + "/analytics", tags=["analytics"])
    app.include_router(rag.router, prefix=settings.api_prefix + "/rag", tags=["rag"])
    return app


app = create_app()

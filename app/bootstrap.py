"""Startup bootstrap for the hosted demo (AUTO_BOOTSTRAP=true).

1. If there are no products: create the sample products, attach their sample reviews and run
   the full enrichment pipeline (LLM aspects + summary, embeddings).
2. If products exist but the vector index is empty (e.g. QDRANT_URL=":memory:" after a restart):
   re-embed the stored reviews only. No LLM calls are repeated.
"""
import logging
import threading

from app.clients.qdrant_client import collection_point_count
from app.db.models import Product
from app.db.session import SessionLocal
from app.demo_data import DEMO_PRODUCTS
from app.pipelines.review_enrichment import embed_reviews_for_product
from app.pipelines.review_enrichment import enrich_reviews_for_product
from app.services.review_service import create_mock_reviews
from app.services.review_service import create_product

logger = logging.getLogger(__name__)

state = {"status": "idle", "error": None}


def run_bootstrap() -> None:
    state["status"] = "running"
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.id).all()
        if not products:
            for item in DEMO_PRODUCTS:
                product = create_product(db, name=item["name"], source="mock", url=None, external_id=None)
                create_mock_reviews(db, product, count=len(item["reviews"]))
                logger.info("Bootstrap: enriching %s", product.name)
                enrich_reviews_for_product(db, product)
        elif collection_point_count() == 0:
            for product in products:
                logger.info("Bootstrap: re-indexing %s", product.name)
                embed_reviews_for_product(db, product)
        state["status"] = "ready"
        logger.info("Bootstrap complete")
    except Exception as e:  # keep serving even if bootstrap fails
        state["status"] = "failed"
        state["error"] = str(e)
        logger.exception("Bootstrap failed")
    finally:
        db.close()


def start_in_background() -> None:
    threading.Thread(target=run_bootstrap, name="bootstrap", daemon=True).start()

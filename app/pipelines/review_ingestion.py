from sqlalchemy.orm import Session

from app.db.models import Product
from app.services.ingestion_service import ingest_reviews


def ingest_product_reviews(db: Session, product: Product) -> int:
    reviews = ingest_reviews(db, product)
    return len(reviews)


from sqlalchemy.orm import Session

from app.db.models import Product
from app.db.models import ProductSummary
from app.db.models import Review
from app.db.models import ReviewAspect
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import get_llm_service
from app.services.rag_service import index_review_embeddings


def embed_reviews_for_product(db: Session, product: Product) -> int:
    """(Re)build vectors for a product's reviews without calling the LLM."""
    reviews = db.query(Review).filter(Review.product_id == product.id).order_by(Review.id).all()
    if reviews:
        vectors = get_embedding_service().embed_batch([r.body for r in reviews])
        index_review_embeddings(reviews, vectors)
    return len(reviews)


def enrich_reviews_for_product(db: Session, product: Product) -> int:
    """Extract aspects + sentiment, index embeddings and write a product summary. Safe to re-run."""
    reviews = db.query(Review).filter(Review.product_id == product.id).order_by(Review.id).all()
    if not reviews:
        return 0

    review_ids = [r.id for r in reviews]
    db.query(ReviewAspect).filter(ReviewAspect.review_id.in_(review_ids)).delete(synchronize_session=False)
    db.query(ProductSummary).filter(ProductSummary.product_id == product.id).delete(synchronize_session=False)
    db.commit()

    llm_service = get_llm_service()
    llm_service.extract_aspects(db, reviews)
    db.commit()

    embed_reviews_for_product(db, product)

    llm_service.generate_product_summary(db, product, reviews)
    db.commit()
    return len(reviews)

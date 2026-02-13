from sqlalchemy.orm import Session

from app.db.models import Product
from app.db.models import Review
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import get_llm_service
from app.services.rag_service import index_review_embedding


def enrich_reviews_for_product(db: Session, product: Product) -> int:
    llm_service = get_llm_service()
    embedding_service = get_embedding_service()
    reviews = db.query(Review).filter(Review.product_id == product.id).all()
    for review in reviews:
        llm_service.extract_aspects_for_review(db, review)
        vector = embedding_service.embed(review.body)
        index_review_embedding(
            review=review,
            vector=vector,
            collection="review_embeddings",
            embedding_model="stub",
        )
    db.commit()
    if reviews:
        llm_service.generate_product_summary(db, product, reviews)
        db.commit()
    return len(reviews)


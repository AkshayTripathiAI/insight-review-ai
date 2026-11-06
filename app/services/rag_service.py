from typing import List

from qdrant_client.http import models as qmodels
from sqlalchemy.orm import Session

from app.clients.qdrant_client import get_qdrant_client
from app.config import get_settings
from app.db.models import Review
from app.schemas.rag import QASource
from app.schemas.rag import SemanticSearchHit


def index_review_embeddings(reviews: List[Review], vectors: List[List[float]]) -> None:
    """Upsert review vectors; the review id is the point id, so re-processing overwrites instead of duplicating."""
    if not reviews:
        return
    points = [
        qmodels.PointStruct(
            id=review.id,
            vector=vector,
            payload={
                "product_id": review.product_id,
                "review_id": review.id,
                "rating": review.rating,
                "text": review.body,
            },
        )
        for review, vector in zip(reviews, vectors)
    ]
    get_qdrant_client().upsert(collection_name=get_settings().qdrant_collection, points=points)


def semantic_search(query_vector: List[float], product_id: int, top_k: int) -> List[SemanticSearchHit]:
    client = get_qdrant_client()
    response = client.query_points(
        collection_name=get_settings().qdrant_collection,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=qmodels.Filter(
            must=[qmodels.FieldCondition(key="product_id", match=qmodels.MatchValue(value=product_id))]
        ),
    )
    hits: List[SemanticSearchHit] = []
    for result in response.points:
        payload = result.payload or {}
        review_id = payload.get("review_id")
        if review_id is None:
            continue
        hits.append(
            SemanticSearchHit(
                review_id=int(review_id),
                score=result.score or 0.0,
                snippet=str(payload.get("text", ""))[:300],
                rating=payload.get("rating"),
            )
        )
    return hits


def build_qa_sources(db: Session, hits: List[SemanticSearchHit]) -> List[QASource]:
    review_ids = [h.review_id for h in hits]
    reviews = db.query(Review).filter(Review.id.in_(review_ids)).all()
    review_by_id = {r.id: r for r in reviews}
    sources: List[QASource] = []
    for hit in hits:
        review = review_by_id.get(hit.review_id)
        if not review:
            continue
        sources.append(QASource(review_id=review.id, score=hit.score, snippet=review.body[:300]))
    return sources

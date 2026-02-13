from typing import List

from qdrant_client.http import models as qmodels
from sqlalchemy.orm import Session

from app.clients.qdrant_client import get_qdrant_client
from app.db.models import Review
from app.schemas.rag import QASource
from app.schemas.rag import SemanticSearchHit


def index_review_embedding(
    review: Review,
    vector: List[float],
    collection: str,
    embedding_model: str,
) -> str:
    client = get_qdrant_client()
    payload = {
        "product_id": review.product_id,
        "review_id": review.id,
        "rating": review.rating,
        "text": review.body,
    }
    point = qmodels.PointStruct(id=None, vector=vector, payload=payload)
    response = client.upsert(collection_name=collection, points=[point])
    if response:
        return str(response)
    return ""


def semantic_search(collection: str, query_vector: List[float], product_id: int, top_k: int) -> List[SemanticSearchHit]:
    client = get_qdrant_client()
    search_result = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
        query_filter=qmodels.Filter(
            must=[qmodels.FieldCondition(key="product_id", match=qmodels.MatchValue(value=product_id))]
        ),
    )
    hits: List[SemanticSearchHit] = []
    for result in search_result:
        payload = result.payload or {}
        snippet = str(payload.get("text", ""))[:200]
        rating = payload.get("rating")
        review_id = payload.get("review_id")
        if review_id is None:
            continue
        hits.append(
            SemanticSearchHit(
                review_id=int(review_id),
                score=result.score or 0.0,
                snippet=snippet,
                rating=rating,
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
        snippet = review.body[:200]
        sources.append(QASource(review_id=review.id, score=hit.score, snippet=snippet))
    return sources


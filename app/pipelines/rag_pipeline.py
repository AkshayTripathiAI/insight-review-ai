from sqlalchemy.orm import Session

from app.db.models import Review
from app.schemas.rag import QAResponse
from app.schemas.rag import SemanticSearchResponse
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import get_llm_service
from app.services.rag_service import build_qa_sources
from app.services.rag_service import semantic_search

QA_SYSTEM = (
    "You answer shoppers' questions about a product using ONLY the customer reviews provided. "
    "Cite reviews inline as [Review <id>]. If the reviews do not answer the question, say so plainly. "
    "Keep answers under 120 words."
)


def run_semantic_search(product_id: int, query: str, top_k: int) -> SemanticSearchResponse:
    query_vector = get_embedding_service().embed(query, is_query=True)
    hits = semantic_search(query_vector=query_vector, product_id=product_id, top_k=top_k)
    return SemanticSearchResponse(hits=hits)


def run_qa(db: Session, product_id: int, question: str, top_k: int) -> QAResponse:
    query_vector = get_embedding_service().embed(question, is_query=True)
    hits = semantic_search(query_vector=query_vector, product_id=product_id, top_k=top_k)
    sources = build_qa_sources(db, hits)
    if not sources:
        return QAResponse(answer="There are no indexed reviews for this product yet.", sources=[])
    bodies = {r.id: r.body for r in db.query(Review).filter(Review.id.in_([s.review_id for s in sources]))}
    context = "\n\n".join(f"[Review {s.review_id}]: {bodies.get(s.review_id, s.snippet)}" for s in sources)
    prompt = f"Reviews:\n{context}\n\nQuestion: {question}"
    answer = get_llm_service().client.generate(prompt, system=QA_SYSTEM)
    return QAResponse(answer=answer.strip(), sources=sources)

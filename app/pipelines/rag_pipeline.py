from sqlalchemy.orm import Session

from app.schemas.rag import QAResponse
from app.schemas.rag import SemanticSearchResponse
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import get_llm_service
from app.services.rag_service import build_qa_sources
from app.services.rag_service import semantic_search


def run_semantic_search(product_id: int, query: str, top_k: int) -> SemanticSearchResponse:
    embedding_service = get_embedding_service()
    query_vector = embedding_service.embed(query)
    hits = semantic_search(collection="review_embeddings", query_vector=query_vector, product_id=product_id, top_k=top_k)
    return SemanticSearchResponse(hits=hits)


def run_qa(db: Session, product_id: int, question: str, top_k: int) -> QAResponse:
    embedding_service = get_embedding_service()
    llm_service = get_llm_service()
    query_vector = embedding_service.embed(question)
    hits = semantic_search(collection="review_embeddings", query_vector=query_vector, product_id=product_id, top_k=top_k)
    sources = build_qa_sources(db, hits)
    context = "\n\n".join(f"Review {s.review_id}: {s.snippet}" for s in sources)
    prompt = f"Answer the question based only on these reviews:\n{context}\n\nQuestion: {question}"
    answer = llm_service.client.generate(prompt)
    return QAResponse(answer=answer, sources=sources)


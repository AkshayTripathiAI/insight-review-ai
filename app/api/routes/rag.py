from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.pipelines.rag_pipeline import run_qa
from app.pipelines.rag_pipeline import run_semantic_search
from app.schemas.rag import QARequest
from app.schemas.rag import QAResponse
from app.schemas.rag import SemanticSearchRequest
from app.schemas.rag import SemanticSearchResponse


router = APIRouter()


@router.post("/products/{product_id}/semantic-search", response_model=SemanticSearchResponse)
def semantic_search_endpoint(
    product_id: int,
    payload: SemanticSearchRequest,
) -> SemanticSearchResponse:
    return run_semantic_search(product_id=product_id, query=payload.query, top_k=payload.top_k)


@router.post("/products/{product_id}/qa", response_model=QAResponse)
def qa_endpoint(
    product_id: int,
    payload: QARequest,
    db: Session = Depends(get_db),
) -> QAResponse:
    return run_qa(db=db, product_id=product_id, question=payload.question, top_k=payload.top_k)


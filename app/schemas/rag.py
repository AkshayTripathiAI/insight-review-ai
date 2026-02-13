from typing import List

from pydantic import BaseModel


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SemanticSearchHit(BaseModel):
    review_id: int
    score: float
    snippet: str
    rating: int | None


class SemanticSearchResponse(BaseModel):
    hits: List[SemanticSearchHit]


class QARequest(BaseModel):
    question: str
    top_k: int = 5


class QASource(BaseModel):
    review_id: int
    score: float
    snippet: str


class QAResponse(BaseModel):
    answer: str
    sources: List[QASource]


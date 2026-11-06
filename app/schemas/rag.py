from typing import List

from pydantic import BaseModel
from pydantic import Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)


class SemanticSearchHit(BaseModel):
    review_id: int
    score: float
    snippet: str
    rating: int | None


class SemanticSearchResponse(BaseModel):
    hits: List[SemanticSearchHit]


class QARequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)


class QASource(BaseModel):
    review_id: int
    score: float
    snippet: str


class QAResponse(BaseModel):
    answer: str
    sources: List[QASource]


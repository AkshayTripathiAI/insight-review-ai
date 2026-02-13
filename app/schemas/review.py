from datetime import date
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReviewRead(BaseModel):
    id: int
    product_id: int
    author: Optional[str]
    rating: Optional[int]
    title: Optional[str]
    body: str
    language: str
    review_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


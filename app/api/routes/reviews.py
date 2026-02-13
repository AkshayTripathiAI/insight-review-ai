from typing import List

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Review
from app.schemas.review import ReviewRead
from app.services.review_service import list_reviews_for_product


router = APIRouter()


@router.get("/product/{product_id}", response_model=List[ReviewRead])
def list_reviews_for_product_endpoint(
    product_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[Review]:
    reviews = list_reviews_for_product(db, product_id, limit=limit, offset=offset)
    return reviews


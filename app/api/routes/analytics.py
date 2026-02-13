from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Product
from app.db.models import ProductSummary
from app.db.models import Review
from app.db.models import ReviewAspect
from app.schemas.analytics import AspectAggregate
from app.schemas.analytics import ProductSummaryRead
from app.services.review_service import get_product


router = APIRouter()


@router.get("/products/{product_id}/aspects", response_model=List[AspectAggregate])
def aggregate_aspects(product_id: int, db: Session = Depends(get_db)) -> List[AspectAggregate]:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    rows = (
        db.query(
            ReviewAspect.aspect,
            func.sum(func.case((ReviewAspect.sentiment == "positive", 1), else_=0)).label("positive_count"),
            func.sum(func.case((ReviewAspect.sentiment == "negative", 1), else_=0)).label("negative_count"),
            func.sum(func.case((ReviewAspect.sentiment == "neutral", 1), else_=0)).label("neutral_count"),
        )
        .join(Review, Review.id == ReviewAspect.review_id)
        .filter(Review.product_id == product_id)
        .group_by(ReviewAspect.aspect)
        .all()
    )
    aggregates: List[AspectAggregate] = []
    for row in rows:
        aggregates.append(
            AspectAggregate(
                aspect=row.aspect,
                positive_count=row.positive_count,
                negative_count=row.negative_count,
                neutral_count=row.neutral_count,
            )
        )
    return aggregates


@router.get("/products/{product_id}/summary", response_model=ProductSummaryRead | None)
def get_product_summary(product_id: int, db: Session = Depends(get_db)) -> ProductSummary | None:
    summary = db.query(ProductSummary).filter(ProductSummary.product_id == product_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return ProductSummaryRead(
        overall_sentiment=summary.overall_sentiment,
        summary_markdown=summary.summary_markdown,
        pros_markdown=summary.pros_markdown,
        cons_markdown=summary.cons_markdown,
    )

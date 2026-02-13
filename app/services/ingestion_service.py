from typing import List

from sqlalchemy.orm import Session

from app.db.models import Product
from app.db.models import Review
from app.services.amazon_scraper import fetch_reviews_for_asin
from app.services.review_service import create_mock_reviews


def ingest_reviews(db: Session, product: Product) -> List[Review]:
    reviews: List[Review] = []
    if product.source == "amazon" and product.external_id:
        scraped = fetch_reviews_for_asin(product.external_id, max_pages=1)
        for index, item in enumerate(scraped):
            review = Review(
                product_id=product.id,
                external_review_id=None,
                author=item.get("reviewerName") or None,
                rating=None,
                title=item.get("reviewTitle") or None,
                body=item.get("reviewText") or "",
                language="en",
                review_date=None,
            )
            db.add(review)
            reviews.append(review)
        db.commit()
        for review in reviews:
            db.refresh(review)
        return reviews
    reviews = create_mock_reviews(db, product, count=10)
    return reviews


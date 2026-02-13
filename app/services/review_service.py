from typing import List

from sqlalchemy.orm import Session

from app.db.models import Product
from app.db.models import Review


def create_product(db: Session, name: str, source: str, url: str | None, external_id: str | None) -> Product:
    product = Product(name=name, source=source, url=url, external_id=external_id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session) -> List[Product]:
    return db.query(Product).order_by(Product.created_at.desc()).all()


def get_product(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def list_reviews_for_product(db: Session, product_id: int, limit: int = 50, offset: int = 0) -> List[Review]:
    return (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def create_mock_reviews(db: Session, product: Product, count: int = 10) -> List[Review]:
    reviews: List[Review] = []
    for i in range(count):
        review = Review(
            product_id=product.id,
            external_review_id=None,
            author=f"User {i + 1}",
            rating=5 if i % 2 == 0 else 4,
            title=f"Mock review {i + 1}",
            body="This is a mock review generated for demonstration of the pipeline.",
            language="en",
            review_date=None,
        )
        db.add(review)
        reviews.append(review)
    db.commit()
    for review in reviews:
        db.refresh(review)
    return reviews


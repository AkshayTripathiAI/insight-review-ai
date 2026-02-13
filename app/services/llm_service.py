from typing import List

from sqlalchemy.orm import Session

from app.clients.llm_client import get_llm_client
from app.db.models import Product
from app.db.models import ProductSummary
from app.db.models import Review
from app.db.models import ReviewAspect


class LLMService:
    def __init__(self) -> None:
        self.client = get_llm_client()

    def extract_aspects_for_review(self, db: Session, review: Review) -> List[ReviewAspect]:
        content = review.body
        summary_prompt = f"Extract a primary aspect and sentiment from this review: {content}"
        _ = self.client.generate(summary_prompt)
        aspect = ReviewAspect(
            review_id=review.id,
            aspect="overall",
            sentiment="neutral",
            confidence=None,
            evidence_span=None,
        )
        db.add(aspect)
        return [aspect]

    def generate_product_summary(self, db: Session, product: Product, reviews: List[Review]) -> ProductSummary:
        joined = "\n\n".join(r.body for r in reviews[:20])
        prompt = f"Summarize how users feel about this product based on these reviews:\n{joined}"
        summary_text = self.client.generate(prompt)
        summary = ProductSummary(
            product_id=product.id,
            overall_sentiment="neutral",
            summary_markdown=summary_text,
            pros_markdown=None,
            cons_markdown=None,
            summary_metadata={"num_reviews": len(reviews)},
            model_version="stub",
        )
        db.add(summary)
        return summary


def get_llm_service() -> LLMService:
    return LLMService()

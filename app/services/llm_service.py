import logging
from typing import Dict
from typing import List

from sqlalchemy.orm import Session

from app.clients.llm_client import get_llm_client
from app.db.models import Product
from app.db.models import ProductSummary
from app.db.models import Review
from app.db.models import ReviewAspect

logger = logging.getLogger(__name__)

SENTIMENTS = {"positive", "negative", "neutral"}

ASPECT_SYSTEM = (
    "You are an analyst that extracts product aspects from customer reviews. "
    "An aspect is a short lowercase noun phrase for a product attribute a reviewer comments on "
    "(for example: battery life, sound quality, comfort, price, build quality, customer service). "
    "Reuse the same aspect name for the same concept across reviews."
)

SUMMARY_SYSTEM = (
    "You are an analyst writing concise, factual product review summaries for a dashboard. "
    "Only use information present in the reviews."
)


def _clean_aspect(name: str) -> str:
    return " ".join(str(name).lower().strip().split())[:60]


class LLMService:
    def __init__(self, batch_size: int = 8) -> None:
        self.client = get_llm_client()
        self.batch_size = batch_size

    def extract_aspects(self, db: Session, reviews: List[Review]) -> List[ReviewAspect]:
        """Extract (aspect, sentiment, evidence) triples for reviews, several reviews per LLM call."""
        created: List[ReviewAspect] = []
        for start in range(0, len(reviews), self.batch_size):
            batch = reviews[start:start + self.batch_size]
            listing = "\n\n".join(
                f"Review {r.id} (rating: {r.rating or 'n/a'}): {(r.title or '').strip()} {r.body.strip()}"
                for r in batch
            )
            prompt = (
                "For each review below, list up to 4 aspects it mentions, each with a sentiment "
                "(positive, negative or neutral) and a short verbatim evidence quote.\n"
                'Return JSON: {"reviews": [{"review_id": <int>, "aspects": '
                '[{"aspect": "...", "sentiment": "...", "evidence": "..."}]}]}\n\n'
                f"{listing}"
            )
            try:
                result = self.client.generate_json(prompt, system=ASPECT_SYSTEM)
            except Exception:
                logger.exception("Aspect extraction failed for a batch; skipping it")
                continue
            by_id: Dict[int, Review] = {r.id: r for r in batch}
            for item in result.get("reviews", []) or []:
                review = by_id.get(_to_int(item.get("review_id")))
                if review is None:
                    continue
                for a in (item.get("aspects") or [])[:4]:
                    aspect = _clean_aspect(a.get("aspect", ""))
                    sentiment = str(a.get("sentiment", "")).lower().strip()
                    if not aspect or sentiment not in SENTIMENTS:
                        continue
                    row = ReviewAspect(
                        review_id=review.id,
                        aspect=aspect,
                        sentiment=sentiment,
                        confidence=None,
                        evidence_span=(str(a.get("evidence") or "")[:500] or None),
                    )
                    db.add(row)
                    created.append(row)
        return created

    def generate_product_summary(self, db: Session, product: Product, reviews: List[Review]) -> ProductSummary:
        joined = "\n".join(f"- ({r.rating or 'n/a'}/5) {r.body.strip()}" for r in reviews[:40])
        prompt = (
            f"Product: {product.name}\n\nCustomer reviews:\n{joined}\n\n"
            "Return JSON with keys: overall_sentiment (positive, negative, mixed or neutral), "
            "summary (2-3 sentences), pros (list of up to 5 short strings), cons (list of up to 5 short strings)."
        )
        data = {}
        try:
            data = self.client.generate_json(prompt, system=SUMMARY_SYSTEM)
        except Exception:
            logger.exception("Summary generation failed")
        pros = [str(p) for p in (data.get("pros") or [])][:5]
        cons = [str(c) for c in (data.get("cons") or [])][:5]
        summary = ProductSummary(
            product_id=product.id,
            overall_sentiment=str(data.get("overall_sentiment") or "neutral").lower(),
            summary_markdown=str(data.get("summary") or "Summary unavailable."),
            pros_markdown="\n".join(f"- {p}" for p in pros) or None,
            cons_markdown="\n".join(f"- {c}" for c in cons) or None,
            summary_metadata={"num_reviews": len(reviews)},
            model_version=self.client.model_name,
        )
        db.add(summary)
        return summary


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_llm_service() -> LLMService:
    return LLMService()

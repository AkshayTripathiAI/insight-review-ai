from pydantic import BaseModel


class AspectAggregate(BaseModel):
    aspect: str
    positive_count: int
    negative_count: int
    neutral_count: int


class ProductSummaryRead(BaseModel):
    overall_sentiment: str
    summary_markdown: str
    pros_markdown: str | None
    cons_markdown: str | None


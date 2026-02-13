from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=True, index=True)
    source = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    summary = relationship("ProductSummary", back_populates="product", uselist=False, cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    external_review_id = Column(String, nullable=True)
    author = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)
    title = Column(Text, nullable=True)
    body = Column(Text, nullable=False)
    language = Column(String, default="en", nullable=False)
    review_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="reviews")
    aspects = relationship("ReviewAspect", back_populates="review", cascade="all, delete-orphan")
    embedding = relationship("ReviewEmbedding", back_populates="review", uselist=False, cascade="all, delete-orphan")


class ReviewAspect(Base):
    __tablename__ = "review_aspects"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, index=True)
    aspect = Column(String, nullable=False, index=True)
    sentiment = Column(String, nullable=False, index=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    evidence_span = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    review = relationship("Review", back_populates="aspects")


class ProductSummary(Base):
    __tablename__ = "product_summaries"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    overall_sentiment = Column(String, nullable=False)
    summary_markdown = Column(Text, nullable=False)
    pros_markdown = Column(Text, nullable=True)
    cons_markdown = Column(Text, nullable=True)
    summary_metadata = Column("metadata", JSONB, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    model_version = Column(String, nullable=True)

    product = relationship("Product", back_populates="summary")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    job_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)


class ReviewEmbedding(Base):
    __tablename__ = "review_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    embedding_model = Column(String, nullable=False)
    vector_dim = Column(Integer, nullable=False)
    qdrant_point_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    review = relationship("Review", back_populates="embedding")

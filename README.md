# InsightReview AI – Amazon Review Intelligence Platform

InsightReview AI turns raw Amazon product reviews into structured insights, semantic search, and RAG-style Q&A using a modular FastAPI backend, PostgreSQL, Qdrant, and a Streamlit dashboard.

This project evolves an original Amazon review scraper into a production-style AI Review Intelligence Platform suitable for a portfolio.

## Features

- Scrape or ingest reviews for Amazon products or mock data
- Store normalized reviews in PostgreSQL
- Extract aspects and sentiments per review using an LLM
- Generate product-level summaries
- Create embeddings and store them in Qdrant
- Semantic search over reviews
- RAG-based Q&A about a product
- FastAPI JSON APIs plus a Streamlit dashboard
- Docker-based local setup

## Architecture Overview

- FastAPI app in `app/` as a modular monolith
- PostgreSQL for relational storage
- Qdrant as vector database for review embeddings
- LLM client abstraction with support for Llama 3.2 via Ollama
- Streamlit dashboard as a thin client on top of the APIs

High-level data flow:

1. Ingest reviews for a product
2. Store reviews in PostgreSQL
3. Run enrichment to extract aspects and sentiments and generate embeddings
4. Push embeddings to Qdrant
5. Expose analytics and RAG endpoints via FastAPI
6. Visualize and query via the Streamlit dashboard

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- Qdrant
- Streamlit
- Selenium and BeautifulSoup for scraping

## Running Locally with Docker

From the project root:

```bash
cd Amazon_review_scrapper
docker-compose up --build
```

Services:

- FastAPI: http://localhost:8000 (docs at `/docs`)
- Streamlit dashboard: http://localhost:8501
- PostgreSQL: localhost:5432
- Qdrant: http://localhost:6333

The FastAPI app will auto-create tables on startup.

## Core API Endpoints

Base URL is `/api/v1`.

- `POST /products`  
  Create a product.

- `GET /products`  
  List products.

- `POST /products/{product_id}/ingest`  
  Ingest reviews for a product. For `source="amazon"` and an `external_id` (ASIN), this uses scraping logic when available, otherwise falls back to mock review generation.

- `POST /products/{product_id}/process`  
  Run aspect extraction, sentiment, embeddings, and summary generation.

- `GET /reviews/product/{product_id}`  
- `GET /analytics/products/{product_id}/aspects`  
- `GET /analytics/products/{product_id}/summary`  

- `POST /rag/products/{product_id}/semantic-search`  
  Semantic search over reviews for a product.

- `POST /rag/products/{product_id}/qa`  
  RAG-based Q&A over reviews.

## LLM Configuration (Llama 3.2 via Ollama)

The LLM client is pluggable. By default it uses an internal stub, but you can use a local Llama 3.2 model via Ollama.

Example Ollama setup:

```bash
ollama pull llama3.2
```

Environment variables for the FastAPI service:

- `LLM_PROVIDER=ollama-llama`
- `LLM_MODEL=llama3.2`
- `LLM_BASE_URL=http://host.docker.internal:11434` (or `http://localhost:11434` if running outside Docker)

The client sends prompts to `LLM_BASE_URL` using the Ollama HTTP API. For JSON-style tasks such as aspect extraction it sends an instruction to respond with machine-readable JSON and parses the response.

## Ingestion and Scraping

There are two main ingestion paths:

- Mock ingestion for fast local testing without external dependencies
- Amazon scraping using Selenium and HTML parsing

For products created with `source="mock"`, ingestion uses synthetic reviews so the full pipeline can be exercised without hitting Amazon.

For products created with `source="amazon"` and a valid ASIN in `external_id`, ingestion uses scraping logic based on Selenium and BeautifulSoup to fetch reviews and normalize them into the internal review schema.

## Testing

Tests use pytest and FastAPI's TestClient.

Install dev dependencies locally:

```bash
pip install -r requirements.txt
```

Make sure PostgreSQL and Qdrant are available, for example by running:

```bash
docker-compose up db qdrant
```

Then run:

```bash
pytest
```

Basic tests cover:

- Creating a product
- Ingesting reviews (mock path)
- Running enrichment
- Calling RAG endpoints

## Qdrant Collection Management

On startup the app ensures a `review_embeddings` collection exists in Qdrant with the configured vector dimension and a cosine distance metric. This keeps vector search consistent and debuggable.

## Roadmap

- Richer aspect extraction and sentiment modeling
- Time-series analytics and multi-product comparisons
- Authentication and API keys
- More robust scraping and error handling
- Expanded test coverage and CI integration


# InsightReview AI

Turn raw product reviews into structured insight: LLM aspect-based sentiment, an AI product summary with pros and cons, semantic search, and question answering over reviews with citations.

**Live demo:** _coming soon_ (the free-tier API sleeps when idle, so the first load can take up to a minute)

> The demo runs on hand-written sample reviews for fictional products (`app/demo_data.py`). They are not real customer reviews.

## What it does

| Stage | How |
|---|---|
| Ingest | Mock/sample reviews, or an optional Selenium + BeautifulSoup Amazon scraper (`source="amazon"` + ASIN) |
| Aspect sentiment | An LLM reads reviews in batches of 8 and returns JSON `{aspect, sentiment, evidence}` triples; invalid labels are dropped |
| Summary | One LLM call per product → overall sentiment, 2–3 sentence summary, pros, cons |
| Embeddings | Gemini `gemini-embedding-001` (768 dims, L2-normalised), stored in Qdrant with the review id as point id |
| Semantic search | Qdrant vector search filtered to the product |
| Q&A (RAG) | Top-k reviews → LLM answer that cites `[Review <id>]`, with sources returned |
| Dashboard | Streamlit: metrics, summary, aspect sentiment chart, Q&A, semantic search |

Enrichment is idempotent: re-processing replaces aspects, the summary and vectors instead of duplicating them.

## Architecture

```
Streamlit dashboard ──HTTP──▶ FastAPI (/api/v1)
                                ├── PostgreSQL   products, reviews, aspects, summaries
                                ├── Qdrant       review vectors (server, Qdrant Cloud, or in-process)
                                ├── LLM          any OpenAI-compatible API (Groq by default) or native Ollama
                                └── Embeddings   Gemini API
```

## Run locally

```bash
cp .env.example .env          # add LLM_API_KEY (Groq) and GOOGLE_API_KEY (Gemini)
docker compose up --build
```

- API: http://localhost:8000/docs
- Dashboard: http://localhost:8501

With `AUTO_BOOTSTRAP=true` (set in `docker-compose.yml`) the API loads the three sample products and runs the full pipeline on first start.

To use a local model instead of Groq: `LLM_PROVIDER=openai LLM_BASE_URL=http://host.docker.internal:11434/v1 LLM_MODEL=llama3.2`.

## API

Base path `/api/v1`.

| Method | Path | |
|---|---|---|
| `POST` | `/products/` | create a product |
| `GET` | `/products/` | list products |
| `POST` | `/products/{id}/ingest` | ingest reviews |
| `POST` | `/products/{id}/process` | aspects + embeddings + summary |
| `GET` | `/reviews/product/{id}` | reviews |
| `GET` | `/analytics/products/{id}/aspects` | aspect sentiment counts (top 15) |
| `GET` | `/analytics/products/{id}/summary` | AI summary |
| `POST` | `/rag/products/{id}/semantic-search` | `{query, top_k}` |
| `POST` | `/rag/products/{id}/qa` | `{question, top_k}` |
| `GET` | `/health` | status, bootstrap state, providers |

## Configuration

See `.env.example`. Key settings:

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `stub` | `openai` (OpenAI-compatible), `ollama-llama`, or `stub` for offline tests |
| `LLM_MODEL` | `openai/gpt-oss-20b` | model name at the provider |
| `EMBED_PROVIDER` | `hash` | `gemini`, or `hash` (deterministic, non-semantic; tests only) |
| `QDRANT_URL` | `http://qdrant:6333` | or `:memory:` for an in-process index rebuilt from Postgres on startup |
| `DEMO_READ_ONLY` | `false` | block create/ingest/process on a public deployment |
| `QA_RATE_LIMIT_PER_HOUR` | `60` | per-client limit on search and Q&A |

## Free-tier deployment

`render.yaml` deploys the API and the dashboard as two free Render web services. Postgres comes from Neon's free tier and Qdrant runs in-process, so the only accounts needed are Render, Neon, Groq and Gemini. After a restart the vector index is rebuilt from Postgres without repeating any LLM calls.

## Tests

```bash
pip install -r requirements.txt
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/reviews pytest
```

Tests run the full pipeline offline (stub LLM, hash embeddings, in-memory Qdrant) against a real Postgres. GitHub Actions runs them on every push.

## Tech stack

Python 3.11 · FastAPI · SQLAlchemy 2 · PostgreSQL · Qdrant · Groq (OpenAI-compatible) · Gemini embeddings · Streamlit · Docker · GitHub Actions

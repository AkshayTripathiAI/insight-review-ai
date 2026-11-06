import time
from collections import defaultdict

from fastapi import HTTPException
from fastapi import Request

from app.config import get_settings


def require_writable() -> None:
    """Block endpoints that create data or spend LLM quota when the app runs as a public demo."""
    if get_settings().demo_read_only:
        raise HTTPException(
            status_code=403,
            detail="This public demo is read-only. Run the project locally to add products and ingest reviews.",
        )


_hits: dict[str, int] = defaultdict(int)


def rate_limit_qa(request: Request) -> None:
    """Fixed-window, per-client limit on LLM-backed endpoints (single-instance, in-process)."""
    limit = get_settings().qa_rate_limit_per_hour
    if limit <= 0:
        return
    forwarded = request.headers.get("x-forwarded-for", "")
    client = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    window = int(time.time() // 3600)
    key = f"{client}:{window}"
    if len(_hits) > 10000:
        _hits.clear()
    _hits[key] += 1
    if _hits[key] > limit:
        raise HTTPException(status_code=429, detail="Hourly question limit reached for this demo. Try again later.")

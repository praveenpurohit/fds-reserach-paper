"""Semantic Scholar API client with global rate limiting.

Free tier allows ~1 req/sec (100 req / 5 min).
A module-level async lock ensures all callers across all agents
are serialized and throttled to stay under the limit.
"""
import asyncio
import time
import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()
BASE_URL = "https://api.semanticscholar.org/graph/v1"

# ── Global Rate Limiter ──────────────────────────────────────────────
# Shared across all functions in this module.
# MIN_INTERVAL = minimum seconds between any two API calls.
MIN_INTERVAL = 1.1  # slightly over 1s to stay safely under the limit
MAX_RETRIES = 3
BASE_DELAY = 3  # seconds for retry backoff

_lock = asyncio.Lock()
_last_call_time: float = 0.0


async def _throttled_request(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    """Execute an HTTP request with global rate limiting and retry on 429."""
    global _last_call_time

    headers = kwargs.pop("headers", {})
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY
    kwargs["headers"] = headers

    for attempt in range(MAX_RETRIES):
        async with _lock:
            # Wait until MIN_INTERVAL has passed since the last call
            now = time.monotonic()
            elapsed = now - _last_call_time
            if elapsed < MIN_INTERVAL:
                await asyncio.sleep(MIN_INTERVAL - elapsed)
            _last_call_time = time.monotonic()

            # Make the actual request
            if method == "GET":
                resp = await client.get(url, **kwargs)
            else:
                resp = await client.post(url, **kwargs)

        if resp.status_code == 429:
            delay = BASE_DELAY * (2 ** attempt)
            print(f"[S2] Rate-limited, waiting {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
            await asyncio.sleep(delay)
            continue

        resp.raise_for_status()
        return resp

    # All retries exhausted
    print("[S2] Max retries exceeded — returning empty response")
    return resp  # Return the last 429 response; callers handle gracefully


# ── Shared HTTP client (reused across calls) ─────────────────────────
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30)
    return _client


# ── Public API ───────────────────────────────────────────────────────

async def search_papers(query: str, limit: int = 20, year_min: Optional[int] = None, year_max: Optional[int] = None) -> list[dict]:
    """Search Semantic Scholar for papers."""
    params = {
        "query": query,
        "limit": min(limit, 10),
        "fields": "title,authors,year,venue,externalIds,abstract,citationCount,url",
    }
    if year_min and year_max:
        params["year"] = f"{year_min}-{year_max}"
    elif year_min:
        params["year"] = f"{year_min}-"

    client = _get_client()
    try:
        resp = await _throttled_request(client, "GET", f"{BASE_URL}/paper/search", params=params)
        if resp.status_code == 429:
            return []
        data = resp.json()
        results = []
        for p in data.get("data", []):
            authors = ", ".join([a.get("name", "") for a in p.get("authors", [])])
            doi = (p.get("externalIds") or {}).get("DOI")
            results.append({
                "title": p.get("title", ""),
                "authors": authors,
                "year": p.get("year"),
                "venue": p.get("venue", ""),
                "doi": doi,
                "abstract": p.get("abstract", ""),
                "citation_count": p.get("citationCount", 0),
                "source": "semantic_scholar",
                "external_id": p.get("paperId", ""),
            })
        return results
    except Exception as e:
        print(f"[S2] search_papers error: {e}")
        return []


async def get_paper_details(paper_id: str) -> Optional[dict]:
    """Get detailed paper info."""
    fields = "title,authors,year,venue,externalIds,abstract,citationCount,citations,references"
    client = _get_client()
    try:
        resp = await _throttled_request(client, "GET", f"{BASE_URL}/paper/{paper_id}", params={"fields": fields})
        if resp.status_code == 429:
            return None
        return resp.json()
    except Exception:
        return None


async def get_citations(paper_id: str, limit: int = 50) -> list[dict]:
    """Get papers that cite this paper."""
    fields = "title,authors,year,venue,externalIds,abstract,citationCount"
    client = _get_client()
    try:
        resp = await _throttled_request(
            client, "GET", f"{BASE_URL}/paper/{paper_id}/citations",
            params={"fields": fields, "limit": limit},
        )
        if resp.status_code == 429:
            return []
        data = resp.json()
        return [item.get("citingPaper", {}) for item in data.get("data", [])]
    except Exception:
        return []


async def get_references(paper_id: str, limit: int = 50) -> list[dict]:
    """Get papers referenced by this paper."""
    fields = "title,authors,year,venue,externalIds,abstract,citationCount"
    client = _get_client()
    try:
        resp = await _throttled_request(
            client, "GET", f"{BASE_URL}/paper/{paper_id}/references",
            params={"fields": fields, "limit": limit},
        )
        if resp.status_code == 429:
            return []
        data = resp.json()
        return [item.get("citedPaper", {}) for item in data.get("data", [])]
    except Exception:
        return []


async def get_recommendations(paper_id: str, limit: int = 10) -> list[dict]:
    """Get recommended papers based on a paper."""
    fields = "title,authors,year,venue,externalIds,abstract,citationCount"
    client = _get_client()
    try:
        resp = await _throttled_request(
            client, "GET",
            "https://api.semanticscholar.org/recommendations/v1/papers/",
            json={"positivePaperIds": [paper_id]},
            params={"fields": fields, "limit": limit},
        )
        if resp.status_code == 429:
            return []
        data = resp.json()
        return data.get("recommendedPapers", [])
    except Exception:
        return []

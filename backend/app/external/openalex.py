import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()
BASE_URL = "https://api.openalex.org"


async def search_works(query: str, limit: int = 20, year_min: Optional[int] = None, year_max: Optional[int] = None) -> list[dict]:
    """Search OpenAlex for works."""
    params = {"search": query, "per_page": min(limit, 50)}
    filters = []
    if year_min:
        filters.append(f"from_publication_date:{year_min}-01-01")
    if year_max:
        filters.append(f"to_publication_date:{year_max}-12-31")
    if filters:
        params["filter"] = ",".join(filters)
    if settings.OPENALEX_EMAIL:
        params["mailto"] = settings.OPENALEX_EMAIL

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(f"{BASE_URL}/works", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for w in data.get("results", []):
                authors = ", ".join([
                    a.get("author", {}).get("display_name", "")
                    for a in w.get("authorships", [])[:5]
                ])
                loc = w.get("primary_location") or {}
                source = loc.get("source") or {}
                venue = source.get("display_name", "") if isinstance(source, dict) else ""
                results.append({
                    "title": w.get("title", ""),
                    "authors": authors,
                    "year": w.get("publication_year"),
                    "venue": venue,
                    "doi": w.get("doi", "").replace("https://doi.org/", "") if w.get("doi") else None,
                    "abstract": _reconstruct_abstract(w.get("abstract_inverted_index")),
                    "citation_count": w.get("cited_by_count", 0),
                    "source": "openalex",
                    "external_id": w.get("id", ""),
                })
            return results
        except Exception as e:
            print(f"OpenAlex search error: {e}")
            return []


def _reconstruct_abstract(inverted_index: Optional[dict]) -> str:
    """Reconstruct abstract from OpenAlex inverted index."""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join([w for _, w in word_positions])

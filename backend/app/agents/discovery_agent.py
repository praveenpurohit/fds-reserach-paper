"""Agent 2: Discovery Agent — Searches external sources for candidate papers."""
from app.external import semantic_scholar, openalex


async def run(state: dict) -> dict:
    query_variants = state.get("query_variants", [state["question"]])
    all_results = []
    seen_titles = set()

    for query in query_variants[:5]:  # Limit to avoid rate limits
        # Search Semantic Scholar
        s2_results = await semantic_scholar.search_papers(query, limit=10)
        for r in s2_results:
            title_lower = r["title"].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                all_results.append(r)

        # Search OpenAlex
        oa_results = await openalex.search_works(query, limit=10)
        for r in oa_results:
            title_lower = r["title"].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                all_results.append(r)

    # Sort by citation count (descending)
    all_results.sort(key=lambda x: x.get("citation_count", 0), reverse=True)

    state["candidate_papers"] = all_results[:50]  # Top 50
    state["discovery_stats"] = {
        "total_found": len(all_results),
        "queries_used": len(query_variants[:5]),
        "sources": ["semantic_scholar", "openalex"],
    }
    return state

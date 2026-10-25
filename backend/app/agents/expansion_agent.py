"""Agent 3: Expansion Agent — Expands paper set via citations, references, and recommendations."""
from app.external import semantic_scholar
from app.services.llm_service import llm_generate, parse_llm_json


async def run(state: dict) -> dict:
    candidates = state.get("candidate_papers", [])
    if not candidates:
        state["expanded_papers"] = []
        state["screened_papers"] = []
        return state

    seen_titles = {p["title"].lower().strip() for p in candidates}
    expanded = list(candidates)

    # Expand top 5 papers via citations + references
    for paper in candidates[:5]:
        ext_id = paper.get("external_id", "")
        if not ext_id:
            continue

        # Get citations
        citations = await semantic_scholar.get_citations(ext_id, limit=10)
        for c in citations:
            if c and c.get("title") and c["title"].lower().strip() not in seen_titles:
                seen_titles.add(c["title"].lower().strip())
                authors = ", ".join([a.get("name", "") for a in c.get("authors", [])])
                expanded.append({
                    "title": c.get("title", ""),
                    "authors": authors,
                    "year": c.get("year"),
                    "venue": c.get("venue", ""),
                    "doi": (c.get("externalIds") or {}).get("DOI"),
                    "abstract": c.get("abstract", ""),
                    "citation_count": c.get("citationCount", 0),
                    "source": "citation_expansion",
                    "external_id": c.get("paperId", ""),
                })

        # Get references
        refs = await semantic_scholar.get_references(ext_id, limit=10)
        for r in refs:
            if r and r.get("title") and r["title"].lower().strip() not in seen_titles:
                seen_titles.add(r["title"].lower().strip())
                authors = ", ".join([a.get("name", "") for a in r.get("authors", [])])
                expanded.append({
                    "title": r.get("title", ""),
                    "authors": authors,
                    "year": r.get("year"),
                    "venue": r.get("venue", ""),
                    "doi": (r.get("externalIds") or {}).get("DOI"),
                    "abstract": r.get("abstract", ""),
                    "citation_count": r.get("citationCount", 0),
                    "source": "reference_expansion",
                    "external_id": r.get("paperId", ""),
                })

    state["expanded_papers"] = expanded

    # Screen for relevance using LLM
    question = state.get("interpreted_question", state["question"])
    papers_for_screening = expanded[:30]  # Screen top 30
    paper_list = "\n".join([
        f"{i+1}. {p['title']} ({p.get('year', 'N/A')}): {(p.get('abstract') or '')[:200]}"
        for i, p in enumerate(papers_for_screening)
    ])

    screen_prompt = f"""Research question: {question}

Papers to screen for relevance (rate each 1-5):
{paper_list}

Return JSON: {{"scores": [{{"index": 1, "score": 5}}, ...]}}
Only include papers scoring 3 or higher."""

    response = await llm_generate(
        "You are a research relevance screener. Rate papers 1-5 for relevance to the question.",
        screen_prompt, json_mode=True
    )
    scores = parse_llm_json(response)

    # Filter by relevance score >= 3
    relevant_indices = set()
    for item in scores.get("scores", []):
        if item.get("score", 0) >= 3:
            relevant_indices.add(item.get("index", 0) - 1)

    if relevant_indices:
        state["screened_papers"] = [papers_for_screening[i] for i in relevant_indices if i < len(papers_for_screening)]
    else:
        state["screened_papers"] = papers_for_screening[:15]  # Fallback

    state["expansion_stats"] = {
        "before_expansion": len(candidates),
        "after_expansion": len(expanded),
        "after_screening": len(state["screened_papers"]),
    }
    return state

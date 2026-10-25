"""Agent 4: Understanding Agent — Extracts structured data, claims, and evidence from papers."""
from app.services.llm_service import llm_generate, parse_llm_json

EXTRACTION_PROMPT = """You are a research paper analysis agent. Extract structured information from this paper.

Return JSON:
{
  "research_question": "...",
  "objective": "...",
  "methodology": "...",
  "dataset": "...",
  "population": "...",
  "experimental_setup": "...",
  "baselines": "...",
  "evaluation_metrics": "...",
  "results_summary": "...",
  "contributions": "...",
  "assumptions": "...",
  "limitations": "...",
  "future_work": "...",
  "claims": [
    {
      "text": "The key finding or claim",
      "claim_type": "finding|conclusion|hypothesis",
      "strength": "strong|moderate|weak",
      "evidence_passage": "Exact quote from paper supporting this claim",
      "page": null,
      "section": "Results"
    }
  ]
}"""


async def run(state: dict) -> dict:
    """Extract structured data from papers that have full text available."""
    papers = state.get("screened_papers", state.get("candidate_papers", []))
    paper_extractions = []
    all_claims = []
    all_evidence = []

    # For papers that have abstracts (from external search), do extraction from abstract
    for paper in papers[:15]:  # Limit to 15 papers
        text = paper.get("abstract", "") or paper.get("full_text", "")
        if not text or len(text) < 50:
            continue

        title = paper.get("title", "Unknown")
        prompt = f"Paper: {title}\nAuthors: {paper.get('authors', 'Unknown')}\nYear: {paper.get('year', 'N/A')}\n\nText:\n{text[:8000]}\n\nExtract all structured information."

        response = await llm_generate(EXTRACTION_PROMPT, prompt, json_mode=True)
        extraction = parse_llm_json(response)

        if extraction:
            extraction["paper_title"] = title
            extraction["paper_authors"] = paper.get("authors", "")
            extraction["paper_year"] = paper.get("year")
            extraction["paper_doi"] = paper.get("doi")
            paper_extractions.append(extraction)

            # Process claims
            for claim_data in extraction.get("claims", []):
                claim = {
                    "text": claim_data.get("text", ""),
                    "claim_type": claim_data.get("claim_type", "finding"),
                    "strength": claim_data.get("strength", "moderate"),
                    "paper_title": title,
                    "paper_authors": paper.get("authors", ""),
                    "paper_year": paper.get("year"),
                    "section": claim_data.get("section", ""),
                    "page": claim_data.get("page"),
                }
                all_claims.append(claim)

                # Link evidence
                if claim_data.get("evidence_passage"):
                    evidence = {
                        "text": claim_data["evidence_passage"],
                        "paper_title": title,
                        "claim_text": claim_data["text"],
                        "page": claim_data.get("page"),
                        "section": claim_data.get("section", ""),
                        "relationship": "SUPPORTS",
                    }
                    all_evidence.append(evidence)

    state["paper_extractions"] = paper_extractions
    state["claims"] = all_claims
    state["evidence_spans"] = all_evidence
    state["understanding_stats"] = {
        "papers_analyzed": len(paper_extractions),
        "claims_extracted": len(all_claims),
        "evidence_spans": len(all_evidence),
    }
    return state

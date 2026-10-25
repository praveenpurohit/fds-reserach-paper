"""Agent 6: Gap Agent — Limitation synthesis, gap generation, counter-evidence validation, opportunity creation."""
from app.services.llm_service import llm_generate, parse_llm_json
from app.external import semantic_scholar

GAP_PROMPT = """You are a research gap analysis agent. Given the research landscape analysis, you must:

1. Synthesize limitations — group by category, count frequency
2. Generate candidate research gaps from:
   - Recurring limitations → "no paper addresses X"
   - Contradictions → "conflicting results need resolution"
   - Missing combinations → "underexplored intersection of A and B"
   - Untested assumptions → "common assumption never validated"
3. For each gap, estimate: novelty (1-10), importance (1-10), feasibility (1-10), evidence_strength (1-10)
4. Suggest specific research questions and hypotheses for each gap

Return JSON:
{
  "limitation_clusters": [
    {"theme": "...", "category": "methodological|dataset|evaluation|generalization|scalability", "count": 5, "papers": ["P1", "P2"]}
  ],
  "research_gaps": [
    {
      "title": "...",
      "description": "...",
      "gap_type": "untested_method|missing_population|missing_dataset|conflicting_findings|underexplored_combination|unresolved_limitation",
      "evidence_papers": ["Paper A", "Paper B"],
      "novelty": 8.0,
      "importance": 9.0,
      "feasibility": 7.0,
      "evidence_strength": 8.5,
      "confidence": 0.85,
      "suggested_questions": ["RQ1", "RQ2"],
      "suggested_hypotheses": ["H1"]
    }
  ]
}"""


async def run(state: dict) -> dict:
    extractions = state.get("paper_extractions", [])
    contradictions = state.get("contradictions", [])
    consensus = state.get("consensus", [])
    themes = state.get("themes", [])

    if not extractions:
        state["limitation_clusters"] = []
        state["research_gaps"] = []
        state["research_opportunities"] = []
        return state

    # Build context
    limitations_text = "\n".join([
        f"- {ext.get('paper_title', 'Unknown')}: {ext.get('limitations', 'N/A')}"
        for ext in extractions if ext.get("limitations")
    ])
    contradictions_text = "\n".join([
        f"- {c.get('topic', '')}: {c.get('claim_a', {}).get('text', '')} vs {c.get('claim_b', {}).get('text', '')}"
        for c in contradictions
    ])
    themes_text = "\n".join([
        f"- {t.get('name', '')}: {t.get('description', '')} ({t.get('paper_count', 0)} papers)"
        for t in themes
    ])

    prompt = f"""Research question: {state.get('interpreted_question', state['question'])}

Papers analyzed: {len(extractions)}

Limitations found:
{limitations_text or 'None identified'}

Contradictions:
{contradictions_text or 'None identified'}

Themes:
{themes_text or 'None identified'}

Consensus points: {len(consensus)}

Analyze limitations, generate candidate research gaps, and create research opportunities."""

    response = await llm_generate(GAP_PROMPT, prompt, json_mode=True)
    result = parse_llm_json(response)

    state["limitation_clusters"] = result.get("limitation_clusters", [])
    candidate_gaps = result.get("research_gaps", [])

    # Validate gaps via counter-evidence search
    validated_gaps = []
    for gap in candidate_gaps:
        gap["validation_status"] = "candidate"
        # Search for counter-evidence
        search_query = gap.get("title", "") + " " + gap.get("description", "")[:100]
        counter_results = await semantic_scholar.search_papers(search_query, limit=5)

        counter_evidence = []
        for cr in counter_results:
            if cr.get("abstract") and gap.get("title", "").lower() in (cr.get("abstract") or "").lower():
                counter_evidence.append({
                    "paper": cr.get("title", ""),
                    "year": cr.get("year"),
                    "abstract": (cr.get("abstract") or "")[:200],
                })

        if counter_evidence:
            gap["counter_evidence"] = counter_evidence
            gap["validation_status"] = "needs_review"
        else:
            gap["validation_status"] = "validated"

        validated_gaps.append(gap)

    state["research_gaps"] = validated_gaps

    # Generate opportunities from validated gaps
    opportunities = []
    for gap in validated_gaps:
        if gap["validation_status"] in ("validated", "needs_review"):
            opportunities.append({
                "title": gap["title"],
                "problem_statement": gap.get("description", ""),
                "current_state": f"Based on analysis of {len(extractions)} papers",
                "missing_evidence": gap.get("description", ""),
                "why_it_matters": f"Gap type: {gap.get('gap_type', 'unknown')}",
                "novelty_score": gap.get("novelty", 5),
                "importance_score": gap.get("importance", 5),
                "feasibility_score": gap.get("feasibility", 5),
                "evidence_strength_score": gap.get("evidence_strength", 5),
                "confidence": gap.get("confidence", 0.5),
                "suggested_questions": gap.get("suggested_questions", []),
                "suggested_hypotheses": gap.get("suggested_hypotheses", []),
                "counter_evidence": gap.get("counter_evidence", []),
                "validation_status": gap["validation_status"],
            })

    # Sort by composite score
    for opp in opportunities:
        opp["composite_score"] = (
            opp["novelty_score"] * 0.25 +
            opp["importance_score"] * 0.3 +
            opp["feasibility_score"] * 0.2 +
            opp["evidence_strength_score"] * 0.25
        )
    opportunities.sort(key=lambda x: x["composite_score"], reverse=True)

    state["research_opportunities"] = opportunities
    state["gap_stats"] = {
        "limitation_clusters": len(state["limitation_clusters"]),
        "candidate_gaps": len(candidate_gaps),
        "validated_gaps": len([g for g in validated_gaps if g["validation_status"] == "validated"]),
        "opportunities_generated": len(opportunities),
    }
    return state

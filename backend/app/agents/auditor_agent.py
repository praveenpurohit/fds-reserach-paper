"""Agent 7: Auditor Agent — Verifies claims, checks evidence, flags issues."""
from app.services.llm_service import llm_generate, parse_llm_json

AUDIT_PROMPT = """You are a research audit agent. Your job is to verify the quality and trustworthiness of research analysis.

Check for:
1. Claims without supporting evidence
2. Overgeneralizations (saying "all studies show..." with few papers)
3. Unsupported strong conclusions
4. Gaps that may already be addressed
5. Contradictions that are actually context-dependent (not true contradictions)
6. Evidence strength assessment

Return JSON:
{
  "audit_results": [
    {
      "type": "warning|error|info",
      "category": "unsupported_claim|overgeneralization|weak_evidence|missing_counter_evidence|citation_issue",
      "message": "...",
      "severity": "high|medium|low",
      "related_item": "claim/gap/contradiction title or text"
    }
  ],
  "confidence_adjustments": [
    {"item": "...", "original_confidence": 0.9, "adjusted_confidence": 0.7, "reason": "..."}
  ],
  "overall_quality": "high|medium|low",
  "overall_confidence": "HIGH|MEDIUM|LOW",
  "summary": "Overall assessment of the research analysis..."
}"""


async def run(state: dict) -> dict:
    claims = state.get("claims", [])
    evidence = state.get("evidence_spans", [])
    contradictions = state.get("contradictions", [])
    gaps = state.get("research_gaps", [])
    opportunities = state.get("research_opportunities", [])

    # Build audit context
    claims_text = "\n".join([
        f"- Claim: {c['text']} (strength: {c.get('strength', 'unknown')}, paper: {c.get('paper_title', 'unknown')})"
        for c in claims[:20]
    ])
    evidence_text = f"Total evidence spans: {len(evidence)}"
    contradictions_text = "\n".join([
        f"- {c.get('topic', '')}: {c.get('contradiction_type', 'unknown')} (confidence: {c.get('confidence', 'N/A')})"
        for c in contradictions
    ])
    gaps_text = "\n".join([
        f"- {g.get('title', '')}: {g.get('validation_status', 'unknown')} (novelty: {g.get('novelty', 'N/A')}, counter-evidence: {len(g.get('counter_evidence', []))})"
        for g in gaps
    ])

    prompt = f"""Audit this research analysis:

Research question: {state.get('interpreted_question', state['question'])}
Papers analyzed: {len(state.get('paper_extractions', []))}

Claims ({len(claims)}):
{claims_text or 'None'}

{evidence_text}

Contradictions ({len(contradictions)}):
{contradictions_text or 'None'}

Research Gaps ({len(gaps)}):
{gaps_text or 'None'}

Opportunities: {len(opportunities)}

Perform a thorough audit. Check for unsupported claims, overgeneralizations, and quality issues."""

    response = await llm_generate(AUDIT_PROMPT, prompt, json_mode=True)
    result = parse_llm_json(response)

    state["audit_results"] = result.get("audit_results", [])
    state["confidence_adjustments"] = result.get("confidence_adjustments", [])
    state["overall_quality"] = result.get("overall_quality", "medium")
    state["overall_confidence"] = result.get("overall_confidence", "MEDIUM")
    state["audit_summary"] = result.get("summary", "Audit completed.")

    state["audit_stats"] = {
        "warnings": len([a for a in state["audit_results"] if a.get("type") == "warning"]),
        "errors": len([a for a in state["audit_results"] if a.get("type") == "error"]),
        "info": len([a for a in state["audit_results"] if a.get("type") == "info"]),
        "overall_quality": state["overall_quality"],
        "overall_confidence": state["overall_confidence"],
    }
    return state

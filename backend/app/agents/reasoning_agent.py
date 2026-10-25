"""Agent 5: Reasoning Agent — Cross-paper comparison, consensus, contradictions."""
from app.services.llm_service import llm_generate, parse_llm_json

REASONING_PROMPT = """You are a cross-paper reasoning agent. Given structured extractions from multiple papers, you must:

1. Compare papers across dimensions (method, dataset, metrics, results, limitations)
2. Identify themes (recurring topics/approaches)
3. Detect consensus (findings supported by 3+ papers)
4. Detect contradictions (conflicting findings on same topic)
5. For each contradiction, explain WHY they differ (dataset, metric, population, methodology, setting)
6. Classify contradictions: true_contradiction, context_dependent, methodological_disagreement, apparent_contradiction

Return JSON:
{
  "comparison": {
    "dimensions": ["method", "dataset", "metrics", "results", "limitations"],
    "papers": [
      {"title": "...", "method": "...", "dataset": "...", "metrics": "...", "results": "...", "limitations": "..."}
    ]
  },
  "themes": [
    {"name": "...", "description": "...", "paper_count": 5, "papers": ["Paper A", "Paper B"]}
  ],
  "consensus": [
    {"finding": "...", "supporting_papers": ["Paper A", "Paper B", "Paper C"], "confidence": 0.9}
  ],
  "contradictions": [
    {
      "topic": "...",
      "claim_a": {"text": "...", "paper": "...", "evidence_strength": "strong"},
      "claim_b": {"text": "...", "paper": "...", "evidence_strength": "moderate"},
      "contradiction_type": "context_dependent",
      "factors": {"dataset": "different distributions", "metric": "accuracy vs F1"},
      "explanation": "...",
      "confidence": 0.8
    }
  ]
}"""


async def run(state: dict) -> dict:
    extractions = state.get("paper_extractions", [])
    claims = state.get("claims", [])

    if not extractions:
        state["comparison"] = {}
        state["themes"] = []
        state["consensus"] = []
        state["contradictions"] = []
        return state

    # Build summary of all papers for the LLM
    papers_summary = []
    for ext in extractions:
        papers_summary.append(
            f"Paper: {ext.get('paper_title', 'Unknown')} ({ext.get('paper_year', 'N/A')})\n"
            f"Method: {ext.get('methodology', 'N/A')}\n"
            f"Dataset: {ext.get('dataset', 'N/A')}\n"
            f"Results: {ext.get('results_summary', 'N/A')}\n"
            f"Limitations: {ext.get('limitations', 'N/A')}\n"
            f"Claims: {', '.join([c['text'] for c in claims if c.get('paper_title') == ext.get('paper_title', '')])}"
        )

    prompt = f"""Research question: {state.get('interpreted_question', state['question'])}

Papers analyzed ({len(extractions)} papers):

{'---'.join(papers_summary)}

Perform cross-paper reasoning: compare, find themes, consensus, and contradictions."""

    response = await llm_generate(REASONING_PROMPT, prompt, json_mode=True)
    result = parse_llm_json(response)

    state["comparison"] = result.get("comparison", {})
    state["themes"] = result.get("themes", [])
    state["consensus"] = result.get("consensus", [])
    state["contradictions"] = result.get("contradictions", [])
    state["reasoning_stats"] = {
        "themes_found": len(state["themes"]),
        "consensus_points": len(state["consensus"]),
        "contradictions_found": len(state["contradictions"]),
    }
    return state

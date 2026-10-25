"""Agent 1: Query Planner — Interprets research question, expands terminology, generates search queries."""
from app.services.llm_service import llm_generate, parse_llm_json

SYSTEM_PROMPT = """You are a research query planning agent. Given a research question, you must:
1. Interpret and clarify the question
2. Extract key concepts
3. Generate synonyms and related terms for each concept
4. Group terms into terminology clusters
5. Generate 5-10 diverse search query variants

Respond in JSON format:
{
  "interpreted_question": "...",
  "concepts": ["concept1", "concept2"],
  "terminology_clusters": [
    {"concept": "...", "terms": ["synonym1", "synonym2", "related1"]}
  ],
  "query_variants": ["query1", "query2", "..."]
}"""


async def run(state: dict) -> dict:
    question = state["question"]
    prompt = f"Research question: {question}\n\nAnalyze this research question and produce the query plan."
    response = await llm_generate(SYSTEM_PROMPT, prompt, json_mode=True)
    result = parse_llm_json(response)

    state["interpreted_question"] = result.get("interpreted_question", question)
    state["concepts"] = result.get("concepts", [])
    state["terminology_clusters"] = result.get("terminology_clusters", [])
    state["query_variants"] = result.get("query_variants", [question])
    return state

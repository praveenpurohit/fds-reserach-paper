"""Research pipeline and results API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.agent_run import AgentRun
from app.schemas import ResearchRunRequest, SearchRequest, SearchResult, AskRequest, AskResponse
from app.services.auth_service import get_current_user
from app.agents.orchestrator import run_full_pipeline
from app.external import semantic_scholar, openalex
from app.utils import embed_text
from app.models.document import DocumentChunk
from app.services.llm_service import llm_generate

router = APIRouter(prefix="/api", tags=["research"])


@router.post("/projects/{project_id}/research/run")
async def start_research_run(
    project_id: str,
    req: ResearchRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start the full 7-agent research pipeline."""
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update project research question
    project.research_question = req.question
    await db.flush()

    # Run the pipeline
    state = await run_full_pipeline(req.question, project_id, db)

    return {
        "status": "completed",
        "question": req.question,
        "interpreted_question": state.get("interpreted_question", ""),
        "concepts": state.get("concepts", []),
        "terminology_clusters": state.get("terminology_clusters", []),
        "query_variants": state.get("query_variants", []),
        "discovery_stats": state.get("discovery_stats", {}),
        "expansion_stats": state.get("expansion_stats", {}),
        "understanding_stats": state.get("understanding_stats", {}),
        "reasoning_stats": state.get("reasoning_stats", {}),
        "gap_stats": state.get("gap_stats", {}),
        "audit_stats": state.get("audit_stats", {}),
        "candidate_papers": len(state.get("candidate_papers", [])),
        "screened_papers": len(state.get("screened_papers", [])),
        "paper_extractions": state.get("paper_extractions", []),
        "claims": state.get("claims", []),
        "comparison": state.get("comparison", {}),
        "themes": state.get("themes", []),
        "consensus": state.get("consensus", []),
        "contradictions": state.get("contradictions", []),
        "limitation_clusters": state.get("limitation_clusters", []),
        "research_gaps": state.get("research_gaps", []),
        "research_opportunities": state.get("research_opportunities", []),
        "audit_results": state.get("audit_results", []),
        "overall_confidence": state.get("overall_confidence", "MEDIUM"),
        "audit_summary": state.get("audit_summary", ""),
        "agent_logs": state.get("agent_logs", []),
    }


@router.get("/projects/{project_id}/agent-runs")
async def get_agent_runs(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.started_at.desc())
    )
    runs = result.scalars().all()
    return [
        {
            "id": r.id, "agent_name": r.agent_name, "status": r.status,
            "started_at": r.started_at, "completed_at": r.completed_at,
            "model_used": r.model_used, "error_message": r.error_message,
            "output": r.output_json,
        } for r in runs
    ]


@router.post("/search/discover", response_model=list[SearchResult])
async def discover_papers(req: SearchRequest, user: User = Depends(get_current_user)):
    """Search external sources for papers."""
    all_results = []
    seen = set()

    if "semantic_scholar" in req.sources:
        results = await semantic_scholar.search_papers(req.query, req.limit, req.year_min, req.year_max)
        for r in results:
            key = r["title"].lower().strip()
            if key not in seen:
                seen.add(key)
                all_results.append(SearchResult(**r))

    if "openalex" in req.sources:
        results = await openalex.search_works(req.query, req.limit, req.year_min, req.year_max)
        for r in results:
            key = r["title"].lower().strip()
            if key not in seen:
                seen.add(key)
                all_results.append(SearchResult(**r))

    return all_results[:req.limit]


@router.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """RAG Q&A over project papers using pgvector."""
    query_embedding = embed_text(req.question)

    # Semantic search using pgvector
    from sqlalchemy import text
    sql = text("""
        SELECT dc.text, dc.page, p.title, p.authors, p.year,
               dc.embedding <=> :embedding AS distance
        FROM document_chunks dc
        JOIN papers p ON dc.paper_id = p.id
        WHERE p.project_id = :project_id
        ORDER BY dc.embedding <=> :embedding
        LIMIT 10
    """)
    result = await db.execute(sql, {"embedding": str(query_embedding), "project_id": req.project_id})
    rows = result.fetchall()

    sources = []
    context_parts = []
    for row in rows:
        sources.append({
            "text": row[0][:300], "page": row[1], "title": row[2],
            "authors": row[3], "year": row[4],
        })
        context_parts.append(f"[{row[2]}, {row[3]}, {row[4]}] (p.{row[1]}): {row[0]}")

    context = "\n\n".join(context_parts)
    system = "You are a research assistant. Answer based ONLY on the provided paper excerpts. Cite sources."
    prompt = f"Context:\n{context}\n\nQuestion: {req.question}"

    answer = await llm_generate(system, prompt)
    return AskResponse(answer=answer, sources=sources)

"""Research Orchestrator — Chains all 7 agents into the full pipeline."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents import query_planner, discovery_agent, expansion_agent
from app.agents import understanding_agent, reasoning_agent, gap_agent, auditor_agent
from app.models.agent_run import AgentRun

AGENTS = [
    ("query_planner", query_planner),
    ("discovery", discovery_agent),
    ("expansion", expansion_agent),
    ("understanding", understanding_agent),
    ("reasoning", reasoning_agent),
    ("gap", gap_agent),
    ("auditor", auditor_agent),
]


async def run_full_pipeline(question: str, project_id: str, db: AsyncSession) -> dict:
    """Run the complete 7-agent research pipeline."""
    state = {
        "question": question,
        "project_id": project_id,
        "agent_logs": [],
    }

    for agent_name, agent_module in AGENTS:
        # Log agent start
        agent_run = AgentRun(
            project_id=project_id,
            agent_name=agent_name,
            status="running",
            input_json={"question": question, "step": agent_name},
        )
        db.add(agent_run)
        await db.flush()

        try:
            state = await agent_module.run(state)
            agent_run.status = "completed"
            agent_run.completed_at = datetime.now(timezone.utc)
            agent_run.output_json = state.get(f"{agent_name}_stats", {})
            state["agent_logs"].append({
                "agent": agent_name,
                "status": "completed",
                "stats": state.get(f"{agent_name}_stats", {}),
            })
        except Exception as e:
            agent_run.status = "failed"
            agent_run.error_message = str(e)
            agent_run.completed_at = datetime.now(timezone.utc)
            state["agent_logs"].append({
                "agent": agent_name,
                "status": "failed",
                "error": str(e),
            })
            # Continue to next agent on non-critical failures
            if agent_name in ("query_planner", "understanding"):
                break  # Critical agents - stop pipeline

        await db.flush()

    return state


async def run_compare_only(paper_extractions: list, question: str, project_id: str, db: AsyncSession) -> dict:
    """Run only the comparison/reasoning pipeline on already-extracted papers."""
    state = {
        "question": question,
        "project_id": project_id,
        "paper_extractions": paper_extractions,
        "claims": [],
        "evidence_spans": [],
        "agent_logs": [],
    }

    for agent_name, agent_module in [("reasoning", reasoning_agent), ("gap", gap_agent), ("auditor", auditor_agent)]:
        try:
            state = await agent_module.run(state)
            state["agent_logs"].append({"agent": agent_name, "status": "completed"})
        except Exception as e:
            state["agent_logs"].append({"agent": agent_name, "status": "failed", "error": str(e)})

    return state

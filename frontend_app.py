"""ResearchIQ — Streamlit Frontend for the 7-Agent Research Pipeline."""
import streamlit as st
import requests
import json
import time

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="ResearchIQ", page_icon="🔬", layout="wide")

# ── Session State ──
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "research_results" not in st.session_state:
    st.session_state.research_results = None


def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}


def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", headers=headers(), timeout=30)
        return r.json() if r.ok else None
    except Exception:
        return None


def api_post(path, data=None, files=None):
    try:
        if files:
            r = requests.post(f"{API_BASE}{path}", data=data, files=files, headers=headers(), timeout=300)
        else:
            r = requests.post(f"{API_BASE}{path}", json=data, headers=headers(), timeout=300)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


# ── Custom CSS ──
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stat-card { background: linear-gradient(135deg, #1e293b, #334155); padding: 1.2rem; border-radius: 12px; border-left: 4px solid #667eea; }
    .agent-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin: 2px; }
    .agent-completed { background: #065f46; color: #6ee7b7; }
    .agent-failed { background: #7f1d1d; color: #fca5a5; }
    .agent-running { background: #1e3a5f; color: #93c5fd; }
    .gap-card { background: #1e293b; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
    .validated { border-left: 4px solid #10b981; }
    .candidate { border-left: 4px solid #f59e0b; }
    .score-bar { height: 8px; border-radius: 4px; background: #334155; }
    .score-fill { height: 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════════════════════════
def auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-header">🔬 ResearchIQ</p>', unsafe_allow_html=True)
        st.markdown("**Agentic AI-Powered Research Paper Analysis & Discovery**")
        st.markdown("---")

        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In", type="primary", use_container_width=True):
                result = api_post("/auth/login", {"email": email, "password": password})
                if "access_token" in result:
                    st.session_state.token = result["access_token"]
                    st.session_state.user = api_get("/auth/me")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with tab2:
            name = st.text_input("Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pass")
            if st.button("Create Account", type="primary", use_container_width=True):
                result = api_post("/auth/signup", {"email": email, "password": password, "name": name})
                if "access_token" in result:
                    st.session_state.token = result["access_token"]
                    st.session_state.user = api_get("/auth/me")
                    st.rerun()
                else:
                    st.error(result.get("error", "Signup failed"))


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        st.markdown(f"### 🔬 ResearchIQ")
        if st.session_state.user:
            st.markdown(f"👤 {st.session_state.user.get('name', 'User')}")
        st.markdown("---")

        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "🔬 Research Workspace",
            "📄 Paper Library",
            "🔍 Discover Papers",
            "⚖️ Compare Papers",
            "📊 Evidence Explorer",
            "⚡ Contradictions",
            "🎯 Gaps & Opportunities",
            "🤖 Agent Activity",
        ], label_visibility="collapsed")

        st.markdown("---")
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

        return page


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════
def dashboard_page():
    st.markdown('<p class="main-header">🏠 Dashboard</p>', unsafe_allow_html=True)

    projects = api_get("/projects") or []

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Projects", len(projects))
    with col2:
        total_papers = sum(p.get("paper_count", 0) for p in projects)
        st.metric("Papers", total_papers)
    with col3:
        st.metric("Agents", "7")
    with col4:
        st.metric("Pipeline", "Active ✅")

    st.markdown("---")

    # Create project
    st.subheader("Create New Project")
    with st.form("new_project"):
        title = st.text_input("Project Title")
        question = st.text_area("Research Question")
        desc = st.text_area("Description (optional)")
        if st.form_submit_button("Create Project", type="primary"):
            result = api_post("/projects", {"title": title, "research_question": question, "description": desc})
            if "id" in result:
                st.success(f"Project created: {result['title']}")
                st.rerun()
            else:
                st.error("Failed to create project")

    # Project list
    if projects:
        st.subheader("Your Projects")
        for p in projects:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{p['title']}**")
                    if p.get("research_question"):
                        st.caption(p["research_question"][:100])
                with col2:
                    st.caption(f"📄 {p.get('paper_count', 0)} papers")
                with col3:
                    if st.button("Open", key=f"open_{p['id']}"):
                        st.session_state.current_project = p
                        st.rerun()


# ══════════════════════════════════════════════════════════════
# RESEARCH WORKSPACE — Run the 7-Agent Pipeline
# ══════════════════════════════════════════════════════════════
def research_workspace_page():
    st.markdown('<p class="main-header">🔬 Research Workspace</p>', unsafe_allow_html=True)

    # Project selector
    projects = api_get("/projects") or []
    if not projects:
        st.warning("Create a project first from the Dashboard.")
        return

    project_names = {p["title"]: p for p in projects}
    selected = st.selectbox("Select Project", list(project_names.keys()))
    project = project_names[selected]
    st.session_state.current_project = project

    st.markdown("---")
    st.markdown("### 🚀 Run 7-Agent Research Pipeline")
    st.markdown("""
    ```
    Question → QueryPlanner → Discovery → Expansion → Understanding → Reasoning → Gap → Auditor
    ```
    """)

    question = st.text_area("Research Question", value=project.get("research_question", ""), height=100)

    if st.button("🚀 Start Research Pipeline", type="primary", use_container_width=True):
        with st.spinner("Running 7-agent pipeline... This may take a few minutes."):
            result = api_post(f"/projects/{project['id']}/research/run", {"question": question, "mode": "full"})

        if "error" in result:
            st.error(f"Pipeline error: {result['error']}")
        else:
            st.session_state.research_results = result
            st.success("✅ Pipeline completed!")

    # Display results
    results = st.session_state.research_results
    if results:
        display_pipeline_results(results)


def display_pipeline_results(results):
    """Render the full pipeline output."""

    # Agent status
    st.markdown("### 🤖 Agent Execution Log")
    for log in results.get("agent_logs", []):
        status_emoji = "✅" if log["status"] == "completed" else "❌"
        st.markdown(f"{status_emoji} **{log['agent']}** — {log['status']}")
        if log.get("stats"):
            st.json(log["stats"])

    st.markdown("---")

    # Query Planner output
    st.markdown("### 1️⃣ Query Planner")
    st.info(f"**Interpreted:** {results.get('interpreted_question', '')}")
    if results.get("concepts"):
        st.markdown("**Concepts:** " + ", ".join(results["concepts"]))
    if results.get("terminology_clusters"):
        for cluster in results["terminology_clusters"]:
            if isinstance(cluster, dict):
                st.markdown(f"- **{cluster.get('concept', '')}**: {', '.join(cluster.get('terms', []))}")
    if results.get("query_variants"):
        with st.expander(f"Search Queries ({len(results['query_variants'])})"):
            for q in results["query_variants"]:
                st.markdown(f"- {q}")

    st.markdown("---")

    # Discovery stats
    st.markdown("### 2️⃣ Literature Discovery")
    ds = results.get("discovery_stats", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Candidates Found", results.get("candidate_papers", 0))
    col2.metric("Queries Used", ds.get("queries_used", 0))
    col3.metric("After Screening", results.get("screened_papers", 0))

    st.markdown("---")

    # Paper extractions
    st.markdown("### 4️⃣ Paper Understanding")
    extractions = results.get("paper_extractions", [])
    if extractions:
        for ext in extractions:
            with st.expander(f"📄 {ext.get('paper_title', 'Unknown')} ({ext.get('paper_year', 'N/A')})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Research Question:** {ext.get('research_question', 'N/A')}")
                    st.markdown(f"**Methodology:** {ext.get('methodology', 'N/A')}")
                    st.markdown(f"**Dataset:** {ext.get('dataset', 'N/A')}")
                with col2:
                    st.markdown(f"**Results:** {ext.get('results_summary', 'N/A')}")
                    st.markdown(f"**Contributions:** {ext.get('contributions', 'N/A')}")
                    st.markdown(f"**Limitations:** {ext.get('limitations', 'N/A')}")

    st.markdown("---")

    # Claims
    claims = results.get("claims", [])
    if claims:
        st.markdown(f"### 📌 Claims Extracted ({len(claims)})")
        for c in claims[:10]:
            strength_color = {"strong": "🟢", "moderate": "🟡", "weak": "🔴"}.get(c.get("strength", ""), "⚪")
            st.markdown(f"{strength_color} **{c['text']}**")
            st.caption(f"From: {c.get('paper_title', '')} | Type: {c.get('claim_type', '')} | Strength: {c.get('strength', '')}")

    st.markdown("---")

    # Themes
    themes = results.get("themes", [])
    if themes:
        st.markdown(f"### 🏷️ Research Themes ({len(themes)})")
        for t in themes:
            if isinstance(t, dict):
                st.markdown(f"- **{t.get('name', '')}**: {t.get('description', '')} ({t.get('paper_count', 0)} papers)")

    # Consensus
    consensus = results.get("consensus", [])
    if consensus:
        st.markdown(f"### ✅ Consensus Points ({len(consensus)})")
        for c in consensus:
            if isinstance(c, dict):
                st.success(f"**{c.get('finding', '')}** — Supported by {len(c.get('supporting_papers', []))} papers (confidence: {c.get('confidence', 'N/A')})")

    st.markdown("---")

    # Contradictions
    contradictions = results.get("contradictions", [])
    if contradictions:
        st.markdown(f"### ⚡ Contradictions ({len(contradictions)})")
        for cont in contradictions:
            if isinstance(cont, dict):
                st.warning(f"**{cont.get('topic', 'Unknown')}**")
                col1, col2 = st.columns(2)
                with col1:
                    claim_a = cont.get("claim_a", {})
                    st.markdown(f"🟢 {claim_a.get('text', 'N/A')} *(from {claim_a.get('paper', 'N/A')})*")
                with col2:
                    claim_b = cont.get("claim_b", {})
                    st.markdown(f"🔴 {claim_b.get('text', 'N/A')} *(from {claim_b.get('paper', 'N/A')})*")
                factors = cont.get("factors", {})
                if factors:
                    st.markdown("**Why they differ:** " + ", ".join([f"{k}: {v}" for k, v in factors.items()]))
                st.caption(f"Type: {cont.get('contradiction_type', 'N/A')} | Confidence: {cont.get('confidence', 'N/A')}")

    st.markdown("---")

    # Gaps & Opportunities
    gaps = results.get("research_gaps", [])
    if gaps:
        st.markdown(f"### 🎯 Research Gaps ({len(gaps)})")
        for g in gaps:
            if isinstance(g, dict):
                status_badge = "✅ Validated" if g.get("validation_status") == "validated" else "⚠️ Candidate"
                st.markdown(f"**{g.get('title', '')}** {status_badge}")
                st.markdown(f"{g.get('description', '')}")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Novelty", f"{g.get('novelty', 0)}/10")
                col2.metric("Importance", f"{g.get('importance', 0)}/10")
                col3.metric("Feasibility", f"{g.get('feasibility', 0)}/10")
                col4.metric("Evidence", f"{g.get('evidence_strength', 0)}/10")
                if g.get("counter_evidence"):
                    st.caption(f"⚠️ Counter-evidence found: {len(g['counter_evidence'])} papers")
                st.markdown("---")

    opportunities = results.get("research_opportunities", [])
    if opportunities:
        st.markdown(f"### 💡 Research Opportunities ({len(opportunities)})")
        for opp in opportunities:
            if isinstance(opp, dict):
                st.markdown(f"#### {opp.get('title', '')}")
                st.markdown(f"**Problem:** {opp.get('problem_statement', '')}")
                if opp.get("suggested_questions"):
                    st.markdown("**Suggested Research Questions:**")
                    for q in opp["suggested_questions"]:
                        st.markdown(f"- {q}")
                st.markdown("---")

    # Audit
    audit = results.get("audit_results", [])
    if audit:
        st.markdown(f"### 🛡️ Audit Results")
        st.info(f"Overall Confidence: **{results.get('overall_confidence', 'N/A')}**")
        st.markdown(results.get("audit_summary", ""))
        for a in audit:
            if isinstance(a, dict):
                icon = {"warning": "⚠️", "error": "❌", "info": "ℹ️"}.get(a.get("type", ""), "•")
                st.markdown(f"{icon} [{a.get('severity', '')}] {a.get('message', '')}")


# ══════════════════════════════════════════════════════════════
# PAPER LIBRARY
# ══════════════════════════════════════════════════════════════
def paper_library_page():
    st.markdown('<p class="main-header">📄 Paper Library</p>', unsafe_allow_html=True)

    projects = api_get("/projects") or []
    if not projects:
        st.warning("Create a project first.")
        return

    project_names = {p["title"]: p for p in projects}
    selected = st.selectbox("Project", list(project_names.keys()), key="paper_proj")
    project = project_names[selected]

    # Upload
    st.subheader("Upload Paper")
    with st.form("upload_paper"):
        file = st.file_uploader("PDF File", type=["pdf"])
        title = st.text_input("Paper Title")
        authors = st.text_input("Authors")
        year = st.number_input("Year", min_value=1900, max_value=2030, value=2024)
        if st.form_submit_button("Upload", type="primary"):
            if file and title:
                result = api_post(
                    "/papers/upload",
                    data={"project_id": project["id"], "title": title, "authors": authors, "year": str(year)},
                    files={"file": (file.name, file, "application/pdf")},
                )
                if "id" in result:
                    st.success(f"Uploaded: {result['title']}")
                else:
                    st.error(f"Upload failed: {result.get('error', 'Unknown error')}")

    # List papers
    papers = api_get(f"/papers/project/{project['id']}") or []
    if papers:
        st.subheader(f"Papers ({len(papers)})")
        for p in papers:
            with st.expander(f"📄 {p['title']} ({p.get('year', 'N/A')})"):
                st.markdown(f"**Authors:** {p.get('authors', 'N/A')}")
                st.markdown(f"**Status:** {p.get('extraction_status', 'N/A')}")
                if p.get("abstract"):
                    st.markdown(f"**Abstract:** {p['abstract'][:300]}...")


# ══════════════════════════════════════════════════════════════
# DISCOVER PAPERS
# ══════════════════════════════════════════════════════════════
def discover_page():
    st.markdown('<p class="main-header">🔍 Discover Papers</p>', unsafe_allow_html=True)

    query = st.text_input("Search query")
    col1, col2 = st.columns(2)
    with col1:
        year_min = st.number_input("Year from", value=2020, min_value=1900, max_value=2030)
    with col2:
        year_max = st.number_input("Year to", value=2026, min_value=1900, max_value=2030)

    if st.button("🔍 Search", type="primary"):
        with st.spinner("Searching Semantic Scholar + OpenAlex..."):
            results = api_post("/search/discover", {
                "query": query, "year_min": year_min, "year_max": year_max, "limit": 20,
            })
        if isinstance(results, list):
            st.success(f"Found {len(results)} papers")
            for r in results:
                with st.container():
                    st.markdown(f"**{r.get('title', '')}** ({r.get('year', 'N/A')})")
                    st.caption(f"{r.get('authors', '')} | {r.get('venue', '')} | Citations: {r.get('citation_count', 0)} | Source: {r.get('source', '')}")
                    if r.get("abstract"):
                        st.markdown(r["abstract"][:200] + "...")
                    st.markdown("---")


# ══════════════════════════════════════════════════════════════
# OTHER PAGES (simplified)
# ══════════════════════════════════════════════════════════════
def compare_page():
    st.markdown('<p class="main-header">⚖️ Compare Papers</p>', unsafe_allow_html=True)
    results = st.session_state.research_results
    if results and results.get("comparison"):
        comp = results["comparison"]
        if comp.get("papers"):
            import pandas as pd
            df = pd.DataFrame(comp["papers"])
            st.dataframe(df, use_container_width=True)
    else:
        st.info("Run the research pipeline first to see comparisons.")


def evidence_page():
    st.markdown('<p class="main-header">📊 Evidence Explorer</p>', unsafe_allow_html=True)
    results = st.session_state.research_results
    if results and results.get("claims"):
        for c in results["claims"][:15]:
            with st.expander(f"📌 {c['text'][:80]}..."):
                st.markdown(f"**Paper:** {c.get('paper_title', '')}")
                st.markdown(f"**Type:** {c.get('claim_type', '')} | **Strength:** {c.get('strength', '')}")
    else:
        st.info("Run the research pipeline first to see evidence.")


def contradictions_page():
    st.markdown('<p class="main-header">⚡ Contradictions</p>', unsafe_allow_html=True)
    results = st.session_state.research_results
    if results and results.get("contradictions"):
        for cont in results["contradictions"]:
            if isinstance(cont, dict):
                st.error(f"**{cont.get('topic', 'Unknown')}** — {cont.get('contradiction_type', '')}")
                st.markdown(f"**Explanation:** {cont.get('explanation', 'N/A')}")
                factors = cont.get("factors", {})
                if factors:
                    cols = st.columns(len(factors))
                    for i, (k, v) in enumerate(factors.items()):
                        cols[i].markdown(f"**{k}:** {v}")
                st.markdown("---")
    else:
        st.info("Run the research pipeline first to see contradictions.")


def gaps_page():
    st.markdown('<p class="main-header">🎯 Gaps & Opportunities</p>', unsafe_allow_html=True)
    results = st.session_state.research_results
    if results and results.get("research_opportunities"):
        for opp in results["research_opportunities"]:
            if isinstance(opp, dict):
                st.markdown(f"### {opp.get('title', '')}")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Novelty", f"{opp.get('novelty_score', 0):.1f}/10")
                col2.metric("Importance", f"{opp.get('importance_score', 0):.1f}/10")
                col3.metric("Feasibility", f"{opp.get('feasibility_score', 0):.1f}/10")
                col4.metric("Evidence", f"{opp.get('evidence_strength_score', 0):.1f}/10")
                st.markdown(f"**Problem:** {opp.get('problem_statement', '')}")
                if opp.get("suggested_questions"):
                    st.markdown("**Research Questions:**")
                    for q in opp["suggested_questions"]:
                        st.markdown(f"- {q}")
                st.markdown("---")
    else:
        st.info("Run the research pipeline first.")


def agent_activity_page():
    st.markdown('<p class="main-header">🤖 Agent Activity</p>', unsafe_allow_html=True)
    results = st.session_state.research_results
    if results and results.get("agent_logs"):
        for log in results["agent_logs"]:
            status_color = "🟢" if log["status"] == "completed" else "🔴"
            st.markdown(f"{status_color} **Agent: {log['agent']}** — {log['status']}")
            if log.get("stats"):
                st.json(log["stats"])
            if log.get("error"):
                st.error(log["error"])
    else:
        st.info("Run the research pipeline to see agent activity.")

    # Show agent runs from DB
    project = st.session_state.current_project
    if project:
        runs = api_get(f"/projects/{project['id']}/agent-runs") or []
        if runs:
            st.subheader("Agent Run History")
            for r in runs[:20]:
                st.markdown(f"**{r['agent_name']}** — {r['status']} — {r.get('started_at', '')}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    if not st.session_state.token:
        auth_page()
        return

    page = sidebar()

    if "Dashboard" in page:
        dashboard_page()
    elif "Research Workspace" in page:
        research_workspace_page()
    elif "Paper Library" in page:
        paper_library_page()
    elif "Discover" in page:
        discover_page()
    elif "Compare" in page:
        compare_page()
    elif "Evidence" in page:
        evidence_page()
    elif "Contradictions" in page:
        contradictions_page()
    elif "Gaps" in page:
        gaps_page()
    elif "Agent Activity" in page:
        agent_activity_page()


if __name__ == "__main__":
    main()

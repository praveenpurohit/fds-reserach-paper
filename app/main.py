"""
AcademicRAG — Research Companion & Literature Intelligence
NotebookLM-grade interface for exploring, interrogating, and synthesizing research papers.
"""
import streamlit as st
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag_engine import get_engine, RAGEngine
from app.config import APP_TITLE, TOP_K_RESULTS, ANTHROPIC_API_KEY, PAPERS_DIR, PAPER_CHUNKS_PATH
from app.academic_features import CitationGenerator, create_academic_features
from add_paper import extract_text_from_pdf, chunk_text, create_paper_id

# ── Page Configuration ────────────────────────────────────────────────
st.set_page_config(
    page_title="AcademicRAG | Research Studio",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Professional Styling (Minimal, Editorial, Clean) ───────────────────
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Tighten container padding */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1400px;
    }

    /* Hide standard menu and footer, keep header visible for sidebar toggle */
    #MainMenu, footer { visibility: hidden; }

    /* Top Studio Bar */
    .studio-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 1.25rem;
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        margin-bottom: 1.25rem;
    }
    .studio-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
        letter-spacing: -0.01em;
    }
    .studio-subtitle {
        font-size: 0.75rem;
        color: #94a3b8;
    }

    /* Metric pill */
    .meta-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 0.75rem;
        color: #cbd5e1;
    }
    .meta-pill strong {
        color: #38bdf8;
    }

    /* Paper list card */
    .paper-entry {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 0.6rem 0.75rem;
        margin-bottom: 0.4rem;
    }
    .paper-entry-name {
        font-size: 0.82rem;
        font-weight: 600;
        color: #e2e8f0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .paper-entry-meta {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 0.15rem;
    }

    /* Clean excerpt callout */
    .source-quote-box {
        background: rgba(15, 23, 42, 0.5);
        border-left: 2px solid #38bdf8;
        padding: 0.7rem 0.9rem;
        border-radius: 0 8px 8px 0;
        margin: 0.4rem 0;
        font-size: 0.83rem;
        line-height: 1.5;
        color: #cbd5e1;
    }

    /* Buttons */
    div[data-testid="stButton"] > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.15s ease-in-out;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.88rem;
        padding: 0.5rem 0.9rem;
    }

    /* Chat Messages */
    .stChatMessage {
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── State Initialization ──────────────────────────────────────────────
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "engine" not in st.session_state:
        st.session_state.engine = None
    if "indexed" not in st.session_state:
        st.session_state.indexed = False
    if "selected_paper" not in st.session_state:
        st.session_state.selected_paper = "all"


# ── Paper Corpus Helper ────────────────────────────────────────────────
def get_corpus_papers():
    if not PAPER_CHUNKS_PATH.exists():
        return []
    try:
        with open(PAPER_CHUNKS_PATH) as f:
            chunks = json.load(f)
        papers = {}
        for c in chunks:
            meta = c.get("metadata", {})
            src = meta.get("source", "Unknown")
            if src not in papers:
                papers[src] = {
                    "source": src,
                    "title": meta.get("title", src),
                    "author": meta.get("author", "Unknown"),
                    "year": meta.get("year", "2024"),
                    "chunks": 0,
                }
            papers[src]["chunks"] += 1
        return list(papers.values())
    except Exception:
        return []


# ── Citation Renderer ─────────────────────────────────────────────────
def render_source(source: dict, idx: int):
    meta = source.get("metadata", {}) or {}
    score = source.get("score", 0) or 0
    text = source.get("text", "") or ""

    author = meta.get("author", "Unknown") or "Unknown"
    year = meta.get("year", "n.d.") or "n.d."
    page = meta.get("page", "?") or "?"
    title = meta.get("title", "Untitled") or "Untitled"

    badge_pct = f"{score * 100:.1f}% Match"
    with st.expander(f"[{idx}] {title} — {author} ({year}), Page {page} ({badge_pct})", expanded=False):
        st.caption(f"File: {meta.get('source', 'Unknown')}")
        if text:
            st.markdown(f'<div class="source-quote-box">{text}</div>', unsafe_allow_html=True)
        else:
            st.caption("No excerpt text available.")


# ── Sidebar ───────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("### Document Library")

        # Upload Area
        uploaded_files = st.file_uploader(
            "Upload Research Paper (PDF)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload PDF research papers to index into your library.",
        )

        if uploaded_files:
            if st.button("Index Uploaded Papers", use_container_width=True, type="primary"):
                PAPERS_DIR.mkdir(parents=True, exist_ok=True)
                chunks_file = PAPER_CHUNKS_PATH

                if chunks_file.exists():
                    with open(chunks_file) as f:
                        all_chunks = json.load(f)
                else:
                    all_chunks = []

                total_new_chunks = 0
                prog = st.progress(0)
                status = st.empty()

                for idx, file in enumerate(uploaded_files):
                    status.text(f"Extracting {file.name}...")
                    save_path = PAPERS_DIR / file.name
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())

                    title = file.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
                    author = "Unknown"
                    year = "2024"
                    paper_id = create_paper_id(author, year, title)

                    all_chunks = [c for c in all_chunks if not c["id"].startswith(f"{paper_id}_")]

                    pages = extract_text_from_pdf(save_path)
                    new_chunks = []
                    for page_num, page_text in pages:
                        p_chunks = chunk_text(page_text)
                        for c_idx, chunk_text_content in enumerate(p_chunks):
                            chunk_id = f"{paper_id}_p{page_num}_c{c_idx}"
                            new_chunks.append({
                                "id": chunk_id,
                                "text": chunk_text_content,
                                "metadata": {
                                    "source": file.name,
                                    "author": author,
                                    "title": title,
                                    "year": year,
                                    "page": str(page_num),
                                },
                            })

                    all_chunks.extend(new_chunks)
                    total_new_chunks += len(new_chunks)
                    prog.progress((idx + 1) / len(uploaded_files))

                with open(chunks_file, "w") as f:
                    json.dump(all_chunks, f, indent=2)

                status.text("Updating vector embeddings...")
                engine = get_engine(use_claude=False, use_claude_code=False)
                indexed_count = engine.index_papers(force_reindex=True)
                st.session_state.indexed = True
                st.toast(f"Successfully indexed {len(uploaded_files)} paper(s)!")
                st.rerun()

        st.divider()

        # Active Paper Scope Filter
        corpus_papers = get_corpus_papers()
        st.markdown("### Active Analysis Scope")
        paper_options = ["all"] + [p["source"] for p in corpus_papers]
        selected_paper = st.selectbox(
            "Filter queries to:",
            options=paper_options,
            format_func=lambda x: "All Uploaded Papers" if x == "all" else x,
            index=0,
            help="Select a specific paper to focus queries and synthesis, or choose 'All Uploaded Papers'.",
        )
        st.session_state.selected_paper = selected_paper

        # Display Papers List
        if corpus_papers:
            st.caption(f"Indexed Documents ({len(corpus_papers)})")
            for p in corpus_papers:
                is_selected = "border-left: 2px solid #38bdf8;" if (selected_paper == p["source"] or selected_paper == "all") else ""
                st.markdown(
                    f"""
                    <div class="paper-entry" style="{is_selected}">
                        <div class="paper-entry-name">{p['source']}</div>
                        <div class="paper-entry-meta">{p['chunks']} chunks • {p['year']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No papers indexed yet. Upload a PDF above.")

        st.divider()

        # Engine Configuration
        with st.expander("Settings & Engine", expanded=False):
            model_choice = st.radio(
                "Model Provider",
                options=["ollama", "claude_code", "claude_api"],
                format_func=lambda x: {
                    "ollama": "Ollama (Local)",
                    "claude_code": "Claude Code (CLI)",
                    "claude_api": "Anthropic API",
                }[x],
                index=0,
            )
            use_claude_code = model_choice == "claude_code"
            use_claude = model_choice == "claude_api"

            top_k = st.slider(
                "Source Excerpts (Top-K)",
                min_value=1,
                max_value=12,
                value=TOP_K_RESULTS,
                help="Number of retrieved chunks per query.",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reindex", use_container_width=True):
                    with st.spinner("Reindexing..."):
                        engine = get_engine(use_claude=use_claude, use_claude_code=use_claude_code)
                        count = engine.index_papers(force_reindex=True)
                        st.session_state.indexed = True
                        st.success(f"Indexed {count} chunks!")
            with col2:
                if st.button("Clear Chat", use_container_width=True):
                    st.session_state.messages = []
                    st.rerun()

        return use_claude, use_claude_code, top_k, selected_paper


# ── Main Studio ────────────────────────────────────────────────────────
def main():
    init_session_state()

    use_claude, use_claude_code, top_k, selected_paper = render_sidebar()

    # Initialize Engine
    engine_changed = (
        st.session_state.engine is None
        or st.session_state.engine.use_claude != use_claude
        or st.session_state.engine.use_claude_code != use_claude_code
    )
    if engine_changed:
        with st.spinner("Connecting to engine..."):
            st.session_state.engine = get_engine(
                use_claude=use_claude, use_claude_code=use_claude_code
            )
            if st.session_state.engine.collection.count() == 0:
                count = st.session_state.engine.index_papers()
                if count > 0:
                    st.toast(f"Indexed {count} paper chunks")

    engine = st.session_state.engine
    corpus_papers = get_corpus_papers()
    stats = engine.get_stats() if engine else {"total_chunks": 0, "total_papers": 0, "llm_model": "None"}

    # Scope Label
    scope_display = "All Documents" if selected_paper == "all" else selected_paper

    # Studio Top Bar
    st.markdown(
        f"""
        <div class="studio-bar">
            <div>
                <h2 class="studio-title">AcademicRAG Studio</h2>
                <div class="studio-subtitle">Grounded Research Synthesis & Literature Intelligence</div>
            </div>
            <div style="display:flex; align-items:center; gap: 0.6rem;">
                <span class="meta-pill">Scope: <strong>{scope_display}</strong></span>
                <span class="meta-pill">Papers: <strong>{len(corpus_papers)}</strong></span>
                <span class="meta-pill">Chunks: <strong>{stats['total_chunks']}</strong></span>
                <span class="meta-pill">Model: <strong>{stats['llm_model']}</strong></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clean Top Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Chat & Inquire",
            "Literature Review",
            "Paper Matrix",
            "Claims & Evidence",
            "Research Gaps",
            "Defense Prep",
        ]
    )

    features = create_academic_features(engine)

    # ── TAB 1: Chat & Inquire ──────────────────────────────────────────
    with tab1:
        st.markdown("**Suggested Inquiries:**")
        q_cols = st.columns(5)
        quick_prompts = [
            ("Core Findings", "What are the core findings and conclusions of the literature?"),
            ("Methodology", "What empirical or theoretical methodologies and datasets are used?"),
            ("Key Claims", "What central claims and hypotheses are evaluated?"),
            ("Limitations", "What limitations or boundaries do the authors note?"),
            ("Contribution", "What is the primary contribution to existing research?"),
        ]

        selected_prompt = None
        for i, (label, prompt_text) in enumerate(quick_prompts):
            with q_cols[i]:
                if st.button(label, use_container_width=True, key=f"quick_{i}"):
                    selected_prompt = prompt_text

        st.divider()

        chat_container = st.container()
        with chat_container:
            if not st.session_state.messages:
                st.markdown(
                    """
                    <div style="text-align: center; padding: 2rem 1rem; color: #94a3b8;">
                        <h4 style="margin-bottom: 0.3rem;">Literature Exploration</h4>
                        <p style="font-size: 0.88rem; max-width: 500px; margin: 0 auto;">
                            Query your uploaded research documents. Each response is grounded in semantic search and includes exact page references.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant" and "sources" in msg:
                        with st.expander(f"Cited Sources ({len(msg['sources'])})", expanded=False):
                            for i, src in enumerate(msg["sources"], 1):
                                render_source(src, i)

        if selected_prompt:
            st.session_state.messages.append({"role": "user", "content": selected_prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(selected_prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing literature..."):
                        answer, sources = engine.query(selected_prompt, top_k=top_k, source_filter=selected_paper)
                    st.markdown(answer)
                    if sources:
                        with st.expander(f"Cited Sources ({len(sources)})", expanded=False):
                            for i, src in enumerate(sources, 1):
                                render_source(src, i)
            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
            st.rerun()

        if user_query := st.chat_input("Ask a question about your literature..."):
            st.session_state.messages.append({"role": "user", "content": user_query})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(user_query)
                with st.chat_message("assistant"):
                    with st.spinner("Searching and synthesizing..."):
                        answer, sources = engine.query(user_query, top_k=top_k, source_filter=selected_paper)
                    if not answer or not answer.strip():
                        st.error("No response generated. Please verify your query.")
                    else:
                        st.markdown(answer)
                    if sources:
                        with st.expander(f"Cited Sources ({len(sources)})", expanded=False):
                            for i, src in enumerate(sources, 1):
                                render_source(src, i)
            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})

    # ── TAB 2: Literature Review ───────────────────────────────────────
    with tab2:
        st.markdown("### Literature Review Drafter")
        st.caption("Synthesize literature into a structured academic literature review draft.")

        c1, c2 = st.columns([3, 1])
        with c1:
            lit_topic = st.text_input(
                "Focus Angle or Topic",
                placeholder="Leave blank to synthesize all aspects of the active scope",
                key="lit_topic",
            )
        with c2:
            section_title = st.text_input("Section Heading", value="Literature Review", key="section_title")

        if st.button("Generate Draft Section", type="primary", key="draft_lit"):
            topic_query = lit_topic.strip() if lit_topic.strip() else "the main findings, core methodology, and theoretical frameworks"
            with st.spinner("Drafting literature review section..."):
                draft, sources = features["literature_drafter"].draft_section(topic_query, section_title)
            st.markdown("---")
            st.markdown(draft)
            st.download_button(
                "Download Markdown Draft",
                draft,
                file_name="literature_review_draft.md",
                mime="text/markdown",
            )
            if sources:
                with st.expander(f"Cited Sources ({len(sources)})"):
                    for i, src in enumerate(sources, 1):
                        render_source(src, i)

    # ── TAB 3: Paper Matrix ────────────────────────────────────────────
    with tab3:
        st.markdown("### Comparative Analysis Matrix")
        st.caption("Compare documents along methodology, data, findings, and limitations.")

        dimension = st.selectbox(
            "Dimension",
            [
                "all",
                "methodology",
                "data_sources",
                "main_findings",
                "theoretical_framework",
                "limitations",
                "policy_implications",
            ],
            format_func=lambda x: "All Dimensions (Full Matrix)" if x == "all" else x.replace("_", " ").title(),
        )

        if st.button("Generate Matrix", type="primary", key="compare"):
            with st.spinner("Building comparative matrix..."):
                comparison, sources = features["paper_comparator"].compare_papers(dimension=dimension)
            st.markdown("---")
            st.markdown(comparison)
            if sources:
                with st.expander("References"):
                    for i, src in enumerate(sources, 1):
                        render_source(src, i)

    # ── TAB 4: Claims & Evidence ───────────────────────────────────────
    with tab4:
        st.markdown("### Claim Extraction & Contradictions")
        st.caption("Extract verifiable claims, evidentiary support, or detect opposing viewpoints.")

        c1, c2 = st.columns([3, 2])
        with c1:
            claim_topic = st.text_input(
                "Topic Focus",
                placeholder="Leave blank to analyze all major claims",
                key="claim_topic",
            )
        with c2:
            claim_type = st.radio(
                "Analysis Mode",
                ["extract", "contradictions"],
                format_func=lambda x: "Extract Claims & Evidence" if x == "extract" else "Find Conflicting Claims",
                horizontal=True,
            )

        if st.button("Run Analysis", type="primary", key="analyze_claims"):
            topic_to_analyze = claim_topic.strip() if claim_topic.strip() else "the central arguments and findings in the literature"
            with st.spinner("Extracting claims..."):
                extractor = features["claim_extractor"]
                if claim_type == "extract":
                    result, sources = extractor.extract_claims(topic_to_analyze)
                else:
                    result, sources = extractor.find_contradictions(topic_to_analyze)
            st.markdown("---")
            st.markdown(result)
            if sources:
                with st.expander("Supporting Citations"):
                    for i, src in enumerate(sources, 1):
                        render_source(src, i)

    # ── TAB 5: Research Gaps ───────────────────────────────────────────
    with tab5:
        st.markdown("### Research Gaps & Opportunities")
        st.caption("Identify understudied areas, methodological gaps, and open questions.")

        gap_topic = st.text_input(
            "Topic Angle (Optional)",
            placeholder="Leave blank to scan all literature",
            key="gap_topic",
        )
        if st.button("Scan for Research Gaps", type="primary", key="find_gaps"):
            with st.spinner("Identifying gaps..."):
                gaps, sources = features["gap_finder"].find_gaps(gap_topic.strip() if gap_topic else None)
            st.markdown("---")
            st.markdown(gaps)
            if sources:
                with st.expander("Supporting Citations"):
                    for i, src in enumerate(sources, 1):
                        render_source(src, i)

    # ── TAB 6: Defense Prep ────────────────────────────────────────────
    with tab6:
        st.markdown("### Defense & Critical Examination Simulator")
        st.caption("Simulate committee defense questions or stress-test claims against the literature.")

        col_def1, col_def2 = st.columns(2)
        with col_def1:
            st.markdown("#### Anticipate Defense Questions")
            if st.button("Generate Committee Questions", use_container_width=True, key="def_questions"):
                with st.spinner("Generating defense questions..."):
                    questions, sources = features["defense_prep"].generate_questions()
                st.markdown(questions)
                if sources:
                    with st.expander("Citations"):
                        for i, src in enumerate(sources, 1):
                            render_source(src, i)

        with col_def2:
            st.markdown("#### Stress-Test a Claim")
            defense_claim = st.text_input(
                "Claim to Defend",
                placeholder="e.g., Automation exposure causes conservative shift",
                key="defense_claim",
            )
            if st.button("Prepare Counterarguments", use_container_width=True, key="def_counter") and defense_claim:
                with st.spinner("Analyzing counterarguments..."):
                    counter, sources = features["defense_prep"].prepare_counterarguments(defense_claim)
                st.markdown(counter)
                if sources:
                    with st.expander("Citations"):
                        for i, src in enumerate(sources, 1):
                            render_source(src, i)


if __name__ == "__main__":
    main()

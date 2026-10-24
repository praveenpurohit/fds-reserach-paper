# AcademicRAG: System Architecture & User Capabilities Specification

A comprehensive technical reference describing the architecture, data flow pipelines, and end-user capabilities of **AcademicRAG**.

---

## 1. System Overview

**AcademicRAG** is a specialized, local-first Retrieval-Augmented Generation (RAG) platform tailored for academic research, thesis writing, and literature intelligence. It allows researchers to upload scholarly PDF papers, automatically parses and vectorizes them into a semantic index, and provides NotebookLM-grade analytical tools (e.g., literature review drafting, comparative analysis matrices, claim and contradiction extraction, research gap scanning, and thesis defense simulations).

```
                      ┌───────────────────────────────────────┐
                      │        User Interface (Streamlit)     │
                      │   - Document Library & Scope Filter   │
                      │   - 6 Research Studio Workspaces      │
                      └──────────────────┬────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
                   ▼                                           ▼
       ┌───────────────────────┐                  ┌────────────────────────┐
       │   Ingestion Engine    │                  │       RAG Engine       │
       │    (add_paper.py)     │                  │     (rag_engine.py)    │
       ├───────────────────────┤                  ├────────────────────────┤
       │ • PyPDF2 Text Parser  │                  │ • ChromaDB Vector Store│
       │ • Sentence Chunking   │                  │ • all-MiniLM-L6-v2 Emb │
       │ • Metadata Extraction │                  │ • Concept Graph Enrich │
       └───────────┬───────────┘                  └────────────┬───────────┘
                   │                                           │
                   ▼                                           ▼
       ┌───────────────────────┐                  ┌────────────────────────┐
       │     Storage Layer     │                  │     LLM Execution      │
       ├───────────────────────┤                  ├────────────────────────┤
       │ • papers/ (PDF files) │                  │ • Local: Ollama        │
       │ • paper_chunks.json   │                  │ • Cloud: Anthropic API │
       │ • data/vectors/ (DB)  │                  │ • CLI: Claude Code     │
       └───────────────────────┘                  └────────────────────────┘
```

---

## 2. Architectural Components

### 2.1 Presentation Layer (`app/main.py`)
Built with Streamlit, optimized for an editorial, distraction-free research experience:
- **Responsive Layout**: Custom typography (Inter & JetBrains Mono) with dark-mode aesthetic.
- **Dynamic Scope Switching**: Allows users to filter queries to a specific uploaded paper or query across the entire indexed corpus.
- **Citation Expanders**: Renders citation source cards with similarity match percentage, document metadata, page numbers, and exact verbatim quotation excerpts.
- **State Management**: Persists chat history, active engine instances, and current corpus statistics (`total_chunks`, `total_papers`, `llm_model`).

### 2.2 Paper Ingestion & Document Processing (`add_paper.py` & `app/main.py`)
1. **PDF Text Extraction**: Uses `PyPDF2` to extract structured text on a page-by-page basis.
2. **Boundary-Aware Chunking**:
   - Fixed character window (`~1500` characters, default overlap of `200` characters).
   - Sentence-boundary awareness (splits on terminal punctuation `. `, preventing truncated sentences).
3. **Metadata Enrichment**:
   - Each chunk retains its `author`, `year`, `title`, `page`, and unique chunk ID format (`{author}_{year}_{title}_p{page}_c{chunk}`).
4. **Deduplication Engine**:
   - Prevents duplicate chunks by clearing prior iterations when re-uploading or updating an existing paper.

### 2.3 Vector Database & Embeddings (`app/rag_engine.py`)
- **Vector Store**: Local persistent `ChromaDB` (`data/vectors/`).
- **Embedding Model**: `all-MiniLM-L6-v2` via `sentence-transformers` (384-dimensional dense vectors, optimized for fast CPU inference).
- **Retrieval Pipeline**: Cosine distance similarity query with optional metadata filtering (`where={"source": paper_name}`).

### 2.4 Multi-Backend LLM Orchestration (`app/rag_engine.py`)
Supports three interchangeable LLM execution paths:
1. **Ollama (Default / Local & Private)**:
   - Zero external data transmission.
   - Fully supports models like `qwen2.5:3b`, `llama3.1:8b`, or `mistral`.
2. **Claude Code CLI**:
   - Direct subprocess execution using Claude Code terminal utilities with automatic ANSI code cleaning and sanitization.
3. **Claude API**:
   - High-throughput direct Anthropic API integration (`claude-sonnet-4-20250514` or specified custom model).
- **Automatic Fallback**: If Claude Code or Claude API is unreachable, the system automatically falls back to the local Ollama instance.

---

## 3. User-Facing Features & Capabilities

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ACADEMIC RESEARCH STUDIO                        │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│ 1. Chat &       │ 2. Literature   │ 3. Paper Matrix  │ 4. Claims &     │
│    Inquire      │    Review       │    (Comparative) │    Evidence     │
├─────────────────┼─────────────────┴──────────────────┼─────────────────┤
│ 5. Research     │ 6. Defense Prep                    │ Scope Selector  │
│    Gaps         │    (Exam Simulation)               │ (Single vs All) │
└─────────────────┴────────────────────────────────────┴─────────────────┘
```

### 1. Document Upload & Ingestion
- **Drag-and-Drop PDFs**: Upload one or multiple research papers simultaneously from the sidebar.
- **One-Click Vector Indexing**: Automatic chunking, progress bar feedback, and vector embedding updates with instant hot-reloading.
- **Active Document Scope**: Filter analysis strictly to a single paper or aggregate synthesis across the entire library.

### 2. Interactive Chat & Inquire
- **Semantic Question Answering**: Grounded in paper excerpts with exact source attribution.
- **Quick Inquiries**: Pre-engineered academic prompts:
  - *Core Findings* (conclusions and main outcomes)
  - *Methodology* (empirical/theoretical datasets and identification strategies)
  - *Key Claims* (primary hypotheses evaluated)
  - *Limitations* (author-declared boundaries)
  - *Contribution* (advancement over prior literature)
- **Verbatim Excerpt Inspection**: Clickable source cards display the exact text snippet and match score percentage.

### 3. Literature Review Drafter
- Formulates a structured academic draft synthesizing the literature.
- Organizes output into:
  1. Introduction & thematic background
  2. Theoretical and empirical arguments across authors
  3. Points of convergence and divergence
  4. Integrative synthesis
- **One-Click Export**: Downloadable `.md` draft ready for import into Obsidian, Word, or LaTeX editors.

### 4. Paper Matrix (Comparative Analysis)
- Generates cross-paper comparison tables across key academic dimensions:
  - `Methodology`
  - `Data Sources & Datasets`
  - `Main Findings`
  - `Theoretical Framework`
  - `Limitations`
  - `Policy Implications`
  - Or a full multidimensional comparison table (`All Dimensions`).

### 5. Claims & Evidence Extractor
- **Claim Extraction Mode**: Isolates major hypotheses, supporting empirical evidence, and confidence rating (Strong / Moderate / Weak).
- **Contradiction Mode**: Identifies competing results across different authors, explaining potential reasons for disagreement (e.g., sample differences, operationalization, methodology).

### 6. Research Gap Finder
- Uncovers understudied areas across:
  - Unanswered theoretical questions
  - Methodological limitations
  - Missing datasets or geographic/demographic contexts
  - Directions proposed by authors for future work

### 7. Thesis & Defense Simulator
- **Anticipate Committee Questions**: Prepares challenging academic defense questions categorized by methodology, theory, limitations, and alternative explanations.
- **Stress-Test a Claim**: Input any claim or hypothesis to prepare counterarguments, defending citations, and boundary caveats.

### 8. Citation & Export Utilities (`app/academic_features.py`)
- Standardized citation generation from source excerpts into:
  - **BibTeX** entries (`@article{authorYear, ...}`)
  - **APA** references
  - **LaTeX** inline citation keys (`\citep{...}`)

---

## 4. Project Directory Map

```
AcademicRAG/
├── app/
│   ├── academic_features.py   # Specialized research tools (Drafter, Matrix, Claims, etc.)
│   ├── config.py              # Central environment and runtime parameters
│   ├── main.py                # Streamlit studio frontend and page controller
│   └── rag_engine.py          # Core ChromaDB retrieval, context assembler & LLM caller
├── data/
│   └── vectors/               # Persistent ChromaDB sqlite and index store
├── papers/
│   ├── paper_chunks.json      # Ingested paper chunks with metadata
│   └── *.pdf                  # Raw uploaded PDF documents
├── add_paper.py               # CLI script for single or batch PDF ingestion
├── build_graph.py             # Knowledge graph synthesis from structured extractions
├── extract_paper.py           # In-depth structured constructs/claims extraction
├── generate_catalog.py        # Rule-based corpus cataloging without LLM calls
├── run_extraction.py          # Batch paper extraction pipeline
├── requirements.txt           # Python dependency specifications
└── run.sh                     # Launch script with automated environment checks
```

---

## 5. System Execution

### Launching the Studio
```bash
# Activate virtual environment
source .venv/bin/activate

# Launch Streamlit app
streamlit run app/main.py
```

### Ingesting via CLI
```bash
python add_paper.py papers/PaperName.pdf "Author Name" "Paper Title" "2024"
```

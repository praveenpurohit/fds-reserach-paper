# ResearchIQ 🔬

An **Agentic AI-Powered Research Paper Analysis and Discovery System** built with a 7-agent pipeline. Upload research papers, ask questions, and let the AI agents discover, analyze, compare, and find gaps across the literature — all from a single dashboard.

> **Stack**: FastAPI + PostgreSQL (pgvector) + Ollama + Streamlit

---

## Features

### 🤖 7-Agent Research Pipeline
A fully orchestrated pipeline where each agent handles one stage of deep research analysis:

| # | Agent | Role |
|---|-------|------|
| 1 | **Query Planner** | Breaks your research question into targeted sub-queries |
| 2 | **Discovery Agent** | Searches Semantic Scholar & OpenAlex for relevant papers |
| 3 | **Expansion Agent** | Follows citation chains — finds papers that cite or are cited by discoveries |
| 4 | **Understanding Agent** | Extracts claims, evidence, methodology from each paper using LLM |
| 5 | **Reasoning Agent** | Finds contradictions and agreements across papers |
| 6 | **Gap Agent** | Identifies research gaps and unexplored areas |
| 7 | **Auditor Agent** | Validates findings and generates final research opportunities |

```
Question → Query Planner → Discovery → Expansion → Understanding → Reasoning → Gaps → Audit → Opportunities
```

### 📄 Paper Management
- Upload PDFs with automatic text extraction and embedding
- Store papers per-project with metadata (title, authors, year, venue)
- Semantic search over your paper corpus using `all-MiniLM-L6-v2` embeddings
- Vector storage in PostgreSQL with pgvector

### 🔍 External Paper Discovery
- **Semantic Scholar** — Search, citations, references, and recommendations
- **OpenAlex** — Broad academic search with filtering by year
- Global rate limiting to avoid API throttling (free tier compatible)

### 🧠 LLM Backends
| Mode | Cost | Setup |
|------|------|-------|
| **Ollama** (local) | Free | `ollama serve` + pull a model |
| **Claude API** | Pay per token | Add `ANTHROPIC_API_KEY` to `.env` |

### 🔐 Authentication
- JWT-based user auth with registration/login
- Project-scoped paper management and research runs

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Streamlit Frontend (port 8501)          │
│  • Auth (Login/Register)                            │
│  • Project Dashboard                                │
│  • Paper Upload & Management                        │
│  • Research Pipeline Runner                         │
│  • Results Explorer (Claims, Gaps, Opportunities)   │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
                       ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (port 8000)             │
│                                                     │
│  ┌─── API Routes ───────────────────────────────┐   │
│  │ /api/auth     — register, login, me          │   │
│  │ /api/projects — CRUD projects                │   │
│  │ /api/papers   — upload, list, search         │   │
│  │ /api/research — run pipeline, search external│   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─── 7-Agent Orchestrator ─────────────────────┐   │
│  │ Query Planner → Discovery → Expansion →      │   │
│  │ Understanding → Reasoning → Gap → Auditor    │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─── Services ─────────────────────────────────┐   │
│  │ LLM Service (Ollama / Claude API)            │   │
│  │ Auth Service (JWT + bcrypt)                  │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌─── External APIs ───────────────────────────┐    │
│  │ Semantic Scholar (rate-limited, with retry)  │   │
│  │ OpenAlex                                     │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│         PostgreSQL + pgvector (port 5433)           │
│  • Users, Projects, Papers                          │
│  • Documents (chunks + vector embeddings)           │
│  • Claims, Evidence, Contradictions                 │
│  • Gaps, Limitations, Opportunities                 │
│  • Agent Run Logs                                   │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- **Python 3.10+**
- **Docker** (for PostgreSQL + pgvector)
- **Ollama** (for local LLM inference)

### 1. Clone and Install

```bash
git clone https://github.com/praveenpurohit/fds-reserach-paper.git
cd fds-reserach-paper

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..
pip install -r requirements.txt
```

### 2. Start PostgreSQL

```bash
docker-compose up -d
```

This starts a `pgvector/pgvector:pg16` container on port **5433** with:
- Database: `research_db`
- User: `research`
- Password: `research123`

### 3. Start Ollama

```bash
ollama serve                 # start the server (if not already running)
ollama pull qwen2.5:3b       # pull a model
```

> You can use any Ollama model — update `OLLAMA_MODEL` in `backend/.env` accordingly.

### 4. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`

### 5. Start the Frontend

Open a **new terminal** (with venv activated):

```bash
streamlit run frontend_app.py
```

- Frontend: `http://localhost:8501`

### Summary of Running Services

| Service | Port | Command |
|---------|------|---------|
| PostgreSQL (Docker) | 5433 | `docker-compose up -d` |
| Ollama | 11434 | `ollama serve` |
| FastAPI Backend | 8000 | `uvicorn app.main:app --reload` |
| Streamlit Frontend | 8501 | `streamlit run frontend_app.py` |

---

## Configuration

All settings are in [`backend/.env`](backend/.env):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...localhost:5433/research_db` | PostgreSQL connection string |
| `SECRET_KEY` | `your-secret-key-...` | JWT signing key (change in production!) |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Local LLM model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `ANTHROPIC_API_KEY` | *(empty)* | Claude API key (optional) |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model for embeddings |
| `SEMANTIC_SCHOLAR_API_KEY` | *(empty)* | Semantic Scholar API key (optional, reduces rate limits) |
| `OPENALEX_EMAIL` | *(empty)* | Email for OpenAlex polite pool (faster responses) |
| `TOP_K_RESULTS` | `10` | Number of vector search results to return |

---

## Project Structure

```
fds-reserach-paper/
├── backend/
│   ├── .env                          # Environment configuration
│   ├── requirements.txt              # Backend Python dependencies
│   ├── app/
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── config.py                 # Pydantic settings (reads .env)
│   │   ├── database.py               # Async SQLAlchemy + pgvector setup
│   │   ├── api/
│   │   │   ├── auth.py               # POST /api/auth/register, login, me
│   │   │   ├── projects.py           # CRUD /api/projects
│   │   │   ├── papers.py             # Upload/list/search /api/papers
│   │   │   └── research.py           # Run pipeline /api/research
│   │   ├── agents/
│   │   │   ├── orchestrator.py       # Chains all 7 agents sequentially
│   │   │   ├── query_planner.py      # Agent 1: Sub-query generation
│   │   │   ├── discovery_agent.py    # Agent 2: External paper search
│   │   │   ├── expansion_agent.py    # Agent 3: Citation chain expansion
│   │   │   ├── understanding_agent.py# Agent 4: Paper comprehension
│   │   │   ├── reasoning_agent.py    # Agent 5: Cross-paper reasoning
│   │   │   ├── gap_agent.py          # Agent 6: Research gap identification
│   │   │   └── auditor_agent.py      # Agent 7: Validation & opportunities
│   │   ├── models/
│   │   │   ├── user.py               # User model
│   │   │   ├── project.py            # Research project model
│   │   │   ├── paper.py              # Paper model (metadata + source)
│   │   │   ├── document.py           # Document chunk + vector embedding
│   │   │   ├── claim.py              # Extracted claims
│   │   │   ├── evidence.py           # Evidence spans
│   │   │   ├── contradiction.py      # Cross-paper contradictions
│   │   │   ├── gap.py                # Research gaps
│   │   │   ├── limitation.py         # Methodological limitations
│   │   │   ├── opportunity.py        # Research opportunities
│   │   │   └── agent_run.py          # Agent execution logs
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── auth_service.py       # JWT token + password hashing
│   │   │   └── llm_service.py        # Ollama / Claude LLM abstraction
│   │   └── external/
│   │       ├── semantic_scholar.py   # S2 API client (rate-limited)
│   │       └── openalex.py           # OpenAlex API client
│   └── uploads/                      # Uploaded PDF storage
├── frontend_app.py                   # Streamlit UI (connects to backend API)
├── docker-compose.yml                # PostgreSQL + pgvector container
├── requirements.txt                  # Frontend/legacy dependencies
├── app/                              # Legacy RAG app (ChromaDB-based)
├── papers/                           # Paper storage (legacy)
├── extractions/                      # Structured extractions (legacy)
├── data/                             # ChromaDB vectors (legacy)
└── docs/                             # Architecture documentation
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create a new user |
| POST | `/api/auth/login` | Login, returns JWT token |
| GET | `/api/auth/me` | Get current user info |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects` | Create a research project |
| GET | `/api/projects` | List user's projects |
| GET | `/api/projects/{id}` | Get project details |
| DELETE | `/api/projects/{id}` | Delete a project |

### Papers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects/{id}/papers/upload` | Upload a PDF paper |
| GET | `/api/projects/{id}/papers` | List papers in project |
| POST | `/api/projects/{id}/papers/search` | Semantic search over papers |

### Research
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects/{id}/research/run` | Run the full 7-agent pipeline |
| POST | `/api/research/search` | Search external APIs (S2 + OpenAlex) |

---

## Technical Details

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI |
| Frontend | Streamlit |
| Database | PostgreSQL 16 + pgvector |
| ORM | SQLAlchemy (async) |
| Embeddings | `all-MiniLM-L6-v2` (384-dim) |
| LLM (Local) | Ollama (qwen2.5:3b default) |
| LLM (Cloud) | Anthropic Claude API |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| PDF Parsing | pdfplumber + PyPDF2 |
| External APIs | Semantic Scholar, OpenAlex |
| Containerization | Docker Compose |

---

## Troubleshooting

### Semantic Scholar 429 Rate Limit
The free tier allows ~1 request/second. The app includes a global rate limiter with retry logic. For better performance, get a free API key from [Semantic Scholar](https://www.semanticscholar.org/product/api#api-key) and add it to `.env`:
```
SEMANTIC_SCHOLAR_API_KEY=your-key-here
```

### OpenAlex Polite Pool
Add your email to `.env` for faster, more reliable OpenAlex responses:
```
OPENALEX_EMAIL=your-email@example.com
```

### Database Connection Issues
Make sure Docker is running and the container is up:
```bash
docker-compose ps
docker-compose up -d
```

### Ollama Not Responding
```bash
ollama serve          # start the server
ollama list           # verify models are installed
```

---

## License

MIT

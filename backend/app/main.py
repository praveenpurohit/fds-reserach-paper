"""ResearchIQ — Agentic AI Research Assistant API."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.api import auth, projects, papers, research

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + pgvector extension."""
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    description="Agentic AI-Powered Research Paper Analysis and Discovery System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(papers.router)
app.include_router(research.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_TITLE}


@app.get("/")
async def root():
    return {
        "app": settings.APP_TITLE,
        "description": "Agentic AI Research Assistant",
        "docs": "/docs",
        "agents": [
            "1. Query Planner",
            "2. Discovery Agent",
            "3. Expansion Agent",
            "4. Understanding Agent",
            "5. Reasoning Agent",
            "6. Gap Agent",
            "7. Auditor Agent",
        ],
        "pipeline": "Question → Discovery → Expansion → Understanding → Reasoning → Gaps → Audit → Opportunities",
    }

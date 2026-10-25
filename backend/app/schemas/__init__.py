from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Auth ──
class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime


# ── Project ──
class ProjectCreate(BaseModel):
    title: str
    research_question: Optional[str] = None
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    research_question: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    title: str
    research_question: Optional[str]
    description: Optional[str]
    status: str
    created_at: datetime
    paper_count: Optional[int] = 0


# ── Paper ──
class PaperCreate(BaseModel):
    title: str
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None

class PaperResponse(BaseModel):
    id: str
    title: str
    authors: Optional[str]
    year: Optional[int]
    venue: Optional[str]
    doi: Optional[str]
    abstract: Optional[str]
    source: str
    extraction_status: str
    created_at: datetime
    # Extraction fields
    research_question: Optional[str] = None
    methodology: Optional[str] = None
    dataset: Optional[str] = None
    results_summary: Optional[str] = None
    contributions: Optional[str] = None
    limitations_text: Optional[str] = None

class PaperImportRequest(BaseModel):
    doi: Optional[str] = None
    semantic_scholar_id: Optional[str] = None


# ── Claim ──
class ClaimResponse(BaseModel):
    id: str
    paper_id: str
    text: str
    claim_type: Optional[str]
    strength: Optional[str]
    confidence: Optional[float]
    page: Optional[int]
    section: Optional[str]
    evidence_count: Optional[int] = 0


# ── Evidence ──
class EvidenceResponse(BaseModel):
    id: str
    paper_id: str
    claim_id: Optional[str]
    text: str
    page: Optional[int]
    section: Optional[str]
    relationship_type: str
    confidence: Optional[float]


# ── Contradiction ──
class ContradictionResponse(BaseModel):
    id: str
    topic: str
    claim_a_text: Optional[str] = None
    claim_b_text: Optional[str] = None
    contradiction_type: Optional[str]
    factors: Optional[dict]
    explanation: Optional[str]
    evidence_strength_a: Optional[str]
    evidence_strength_b: Optional[str]
    confidence: Optional[float]


# ── Gap ──
class GapResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    gap_type: Optional[str]
    validation_status: str
    novelty: Optional[float]
    importance: Optional[float]
    feasibility: Optional[float]
    evidence_strength: Optional[float]
    confidence: Optional[float]
    counter_evidence: Optional[list] = None


# ── Opportunity ──
class OpportunityResponse(BaseModel):
    id: str
    title: str
    problem_statement: Optional[str]
    current_state: Optional[str]
    missing_evidence: Optional[str]
    why_it_matters: Optional[str]
    novelty_score: Optional[float]
    importance_score: Optional[float]
    feasibility_score: Optional[float]
    evidence_strength_score: Optional[float]
    confidence: Optional[float]
    suggested_questions: Optional[list]
    suggested_hypotheses: Optional[list]


# ── Research Run ──
class ResearchRunRequest(BaseModel):
    question: str
    mode: str = "full"  # full, compare, gaps_only

class AgentRunResponse(BaseModel):
    id: str
    agent_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    model_used: Optional[str]


# ── Search ──
class SearchRequest(BaseModel):
    query: str
    sources: list[str] = ["semantic_scholar", "openalex"]
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    limit: int = 20

class SearchResult(BaseModel):
    title: str
    authors: Optional[str]
    year: Optional[int]
    venue: Optional[str]
    doi: Optional[str]
    abstract: Optional[str]
    citation_count: Optional[int] = 0
    source: str
    relevance_score: Optional[float] = None


# ── Report ──
class ReportRequest(BaseModel):
    report_type: str  # literature_review, comparison, gap, opportunity

class ReportResponse(BaseModel):
    id: str
    report_type: str
    content: str
    created_at: datetime


# ── Ask (RAG Q&A) ──
class AskRequest(BaseModel):
    question: str
    project_id: str

class AskResponse(BaseModel):
    answer: str
    sources: list[dict]

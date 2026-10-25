import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.paper import Paper
from app.models.document import DocumentSection, DocumentChunk
from app.schemas import PaperResponse, PaperImportRequest
from app.services.auth_service import get_current_user
from app.utils import extract_pdf_text, chunk_text, detect_sections, embed_batch

router = APIRouter(prefix="/api/papers", tags=["papers"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=PaperResponse)
async def upload_paper(
    project_id: str = Form(...),
    title: str = Form(...),
    authors: str = Form(""),
    year: int = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Save PDF
    file_path = os.path.join(UPLOAD_DIR, f"{project_id}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create paper record
    paper = Paper(
        project_id=project_id, title=title, authors=authors, year=year,
        pdf_path=file_path, source="upload", extraction_status="processing",
    )
    db.add(paper)
    await db.flush()

    # Process PDF
    try:
        pages = extract_pdf_text(file_path)
        full_text = "\n\n".join([p["text"] for p in pages])

        # Detect sections
        sections = detect_sections(full_text)
        for sec in sections:
            doc_section = DocumentSection(
                paper_id=paper.id, heading=sec["heading"],
                text=sec["text"], section_type=sec["type"],
            )
            db.add(doc_section)
            await db.flush()

            # Chunk each section
            chunks = chunk_text(sec["text"])
            if chunks:
                embeddings = embed_batch(chunks)
                for idx, (chunk_text_val, emb) in enumerate(zip(chunks, embeddings)):
                    doc_chunk = DocumentChunk(
                        section_id=doc_section.id, paper_id=paper.id,
                        text=chunk_text_val, chunk_index=idx, embedding=emb,
                    )
                    db.add(doc_chunk)

        paper.abstract = sections[0]["text"][:500] if sections else ""
        paper.extraction_status = "done"
    except Exception as e:
        paper.extraction_status = "failed"
        print(f"PDF processing error: {e}")

    await db.flush()
    return PaperResponse(
        id=paper.id, title=paper.title, authors=paper.authors, year=paper.year,
        venue=paper.venue, doi=paper.doi, abstract=paper.abstract,
        source=paper.source, extraction_status=paper.extraction_status,
        created_at=paper.created_at,
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperResponse(
        id=paper.id, title=paper.title, authors=paper.authors, year=paper.year,
        venue=paper.venue, doi=paper.doi, abstract=paper.abstract,
        source=paper.source, extraction_status=paper.extraction_status,
        created_at=paper.created_at, research_question=paper.research_question,
        methodology=paper.methodology, dataset=paper.dataset,
        results_summary=paper.results_summary, contributions=paper.contributions,
        limitations_text=paper.limitations_text,
    )


@router.get("/project/{project_id}", response_model=list[PaperResponse])
async def list_project_papers(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Paper).where(Paper.project_id == project_id).order_by(Paper.created_at.desc()))
    papers = result.scalars().all()
    return [
        PaperResponse(
            id=p.id, title=p.title, authors=p.authors, year=p.year,
            venue=p.venue, doi=p.doi, abstract=p.abstract,
            source=p.source, extraction_status=p.extraction_status, created_at=p.created_at,
        ) for p in papers
    ]

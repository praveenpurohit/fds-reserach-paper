import os
import pdfplumber
from pathlib import Path
from sentence_transformers import SentenceTransformer
from app.config import get_settings

settings = get_settings()

# Singleton embedding model
_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.encode(texts).tolist()


def extract_pdf_text(pdf_path: str) -> list[dict]:
    """Extract text from PDF, returns list of {page, text} dicts."""
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"page": i + 1, "text": text.strip()})
    except Exception:
        # Fallback to PyPDF2
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"page": i + 1, "text": text.strip()})
    return pages


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap // 5:]) if len(words) > overlap // 5 else ""
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk += " " + sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def detect_sections(full_text: str) -> list[dict]:
    """Heuristic section detection from paper text."""
    import re
    section_patterns = [
        r'^(?:(\d+\.?\s*)?)(abstract|introduction|background|related work|methodology|methods?|'
        r'experimental? setup|results?|discussion|conclusion|limitations?|future work|references)',
    ]
    lines = full_text.split('\n')
    sections = []
    current_section = {"heading": "Header", "type": "header", "text": ""}

    for line in lines:
        is_heading = False
        for pattern in section_patterns:
            if re.match(pattern, line.strip(), re.IGNORECASE) and len(line.strip()) < 100:
                if current_section["text"].strip():
                    sections.append(current_section)
                heading = line.strip()
                section_type = re.sub(r'^\d+\.?\s*', '', heading).lower().replace(' ', '_')
                current_section = {"heading": heading, "type": section_type, "text": ""}
                is_heading = True
                break
        if not is_heading:
            current_section["text"] += line + "\n"

    if current_section["text"].strip():
        sections.append(current_section)
    return sections

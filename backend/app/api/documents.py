from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from starlette.concurrency import run_in_threadpool

from app.api.deps import Services, get_services
from app.bots import NORTHWIND
from app.errors import AppError
from app.ingest.service import ingest_pdf
from app.models import Document, DocumentOut, ErrorResponse

router = APIRouter(prefix="/documents", tags=["documents"])

SAMPLE_PDF = NORTHWIND.knowledge_base
PDF_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream", ""}
SAMPLE_QUESTIONS = list(NORTHWIND.suggestions)
ERRORS = {code: {"model": ErrorResponse} for code in (404, 413, 415, 422)}


def _out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        name=doc.name,
        pages=doc.pages,
        chunks=len(doc.chunks),
        suggestions=doc.suggestions,
    )


@router.post("", response_model=DocumentOut, status_code=201, responses=ERRORS)
async def upload_document(
    services: Annotated[Services, Depends(get_services)],
    file: Annotated[UploadFile, File(description="A text-based PDF")],
) -> DocumentOut:
    settings = services.settings
    name = Path(file.filename or "document.pdf").name
    if (file.content_type or "") not in PDF_TYPES and not name.lower().endswith(".pdf"):
        raise AppError(415, "invalid_file", "Please upload a PDF file.")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise AppError(
            413, "file_too_large", f"That file is over the {settings.max_upload_mb} MB limit."
        )
    if not data:
        raise AppError(422, "invalid_file", "That file is empty.")
    doc = await run_in_threadpool(ingest_pdf, name, data, settings)
    services.documents.add(doc)
    return _out(doc)


@router.post("/sample", response_model=DocumentOut, status_code=201)
async def load_sample(services: Annotated[Services, Depends(get_services)]) -> DocumentOut:
    """Load the sample help center as a temporary document, for trying the flow without a file."""
    data = await run_in_threadpool(SAMPLE_PDF.read_bytes)
    doc = await run_in_threadpool(
        ingest_pdf, SAMPLE_PDF.name, data, services.settings, SAMPLE_QUESTIONS
    )
    services.documents.add(doc)
    return _out(doc)


@router.get("/{doc_id}", response_model=DocumentOut, responses=ERRORS)
def get_document(doc_id: str, services: Annotated[Services, Depends(get_services)]) -> DocumentOut:
    doc = services.documents.get(doc_id)
    if doc is None:
        raise AppError(404, "not_found", "That document doesn't exist or has expired.")
    return _out(doc)

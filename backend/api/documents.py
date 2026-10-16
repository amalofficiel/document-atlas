from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config import DOCUMENTS_DIR

router = APIRouter()


def source_url(filename: str, page: int) -> str:
    """PDF pages are one-based, as in extract_pdf_pages."""
    return f"/api/documents/{quote(filename, safe='')}#page={page}"


def resolve_document(filename: str):
    # Only expose uniquely named PDFs inside the document directory.
    if "/" in filename or "\\" in filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=404, detail="Document introuvable.")

    root = DOCUMENTS_DIR.resolve()
    matches = [
        path
        for path in root.rglob("*.pdf")
        if path.name == filename
        and path.is_file()
        and path.resolve().is_relative_to(root)
    ]
    if len(matches) != 1:
        raise HTTPException(status_code=404, detail="Document introuvable.")

    return matches[0]


@router.get("/api/documents/{filename}")
def get_document(filename: str):
    return FileResponse(
        resolve_document(filename),
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="inline",
    )

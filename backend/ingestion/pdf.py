from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

# Valeurs uniques pour tout le projet (indexation Qdrant ET graphe).
# Si vous les changez, il faut réindexer.
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


def extract_pdf_pages(pdf_path: str | Path) -> list[dict]:
    """Extrait le texte page par page."""

    pdf_path = Path(pdf_path)
    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())

        if not text:
            continue

        pages.append(
            {
                "filename": pdf_path.name,
                "page": page_number,
                "text": text,
            }
        )

    return pages


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Découpe un texte en morceaux, de préférence à la fin d'une phrase."""

    if not text:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap doit être inférieur à chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        if end < text_length:
            # 1. On essaie de couper à la fin d'une phrase
            last_punctuation = max(
                chunk.rfind(". "),
                chunk.rfind("! "),
                chunk.rfind("? "),
            )

            if last_punctuation > chunk_size // 2:
                end = start + last_punctuation + 1
            else:
                # 2. Sinon, on coupe au dernier espace (pas au milieu d'un mot)
                last_space = chunk.rfind(" ")
                if last_space > chunk_size // 2:
                    end = start + last_space

            chunk = text[start:end]

        chunk = chunk.strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        # Le départ avance toujours (évite une boucle infinie)
        next_start = max(end - chunk_overlap, start + 1)

        # On évite de commencer un chunk au milieu d'un mot
        while next_start < end and text[next_start - 1] != " ":
            next_start += 1

        start = next_start

    return chunks


def chunk_pdf(
    pdf_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """Retourne les chunks d'un PDF, avec nom de fichier et numéro de page."""

    pages = extract_pdf_pages(pdf_path)

    results = []
    chunk_id = 0

    for page in pages:
        page_chunks = chunk_text(
            page["text"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk in page_chunks:
            results.append(
                {
                    "chunk_id": chunk_id,
                    "filename": page["filename"],
                    "page": page["page"],
                    "text": chunk,
                }
            )
            chunk_id += 1

    return results

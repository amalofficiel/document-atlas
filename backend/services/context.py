"""Read complete cited pages and keep source numbering synchronized."""

import logging
import re
from functools import lru_cache

from fastapi import HTTPException

from backend.api.documents import resolve_document, source_url
from backend.ingestion.pdf import extract_pdf_pages

logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
def _read_pages(path: str, modified: int) -> dict:
    return {item["page"]: item["text"] for item in extract_pdf_pages(path)}


def build_context(results: list[dict]) -> tuple[str, list[dict]]:
    sources, parts, seen = [], [], set()
    for result in results:
        filename, page = result.get("filename"), result.get("page")
        if (
            not filename
            or not isinstance(page, int)
            or page < 1
            or (filename, page) in seen
        ):
            continue
        try:
            path = resolve_document(filename)
            text = _read_pages(str(path), path.stat().st_mtime_ns).get(page)
        except (HTTPException, OSError):
            logger.warning("Source unavailable: %s", filename)
            continue
        if not text:
            continue
        seen.add((filename, page))
        match = re.search(r"(?:19|20)\d{2}", filename)
        sources.append(
            {
                "filename": filename,
                "page": page,
                "url": source_url(filename, page),
                "year": result.get("year") or (int(match.group()) if match else None),
                "retrieval_type": result.get("retrieval_type", "hybrid"),
                "excerpt": text[:200],
                "retrieval_scores": result.get("retrieval_scores", {}),
                "retrieval_ranks": result.get("retrieval_ranks", {}),
                "fusion_score": result.get("fusion_score"),
                "rerank_score": result.get("rerank_score"),
            }
        )
        parts.append(f"[Source {len(sources)} : {filename}, page {page}]\n{text}")
    return "\n\n".join(parts), sources

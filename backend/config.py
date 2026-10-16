"""Application settings shared by the API and the indexing command."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DOCUMENTS_DIR = BASE_DIR / "documents"
QDRANT_DIR = BASE_DIR / "data" / "qdrant"
COLLECTION_NAME = "atlas_documents"
SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", "0.5"))
RRF_K = int(os.getenv("RRF_K", "60"))
CANDIDATE_K = int(os.getenv("CANDIDATE_K", "100"))
USE_GRAPH_RAG = os.getenv("USE_GRAPH_RAG", "false").lower() == "true"
_threshold = os.getenv("RERANK_THRESHOLD", "").strip()
RERANK_THRESHOLD = float(_threshold) if _threshold else None
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
if not 0 <= SEMANTIC_WEIGHT <= 1 or RRF_K < 1 or not 1 <= CANDIDATE_K <= 1000:
    raise ValueError(
        "Invalid retrieval settings: SEMANTIC_WEIGHT ∈ [0,1], RRF_K ≥ 1, CANDIDATE_K ∈ [1,1000]."
    )

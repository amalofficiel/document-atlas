"""FastAPI entry point. Run: python -m uvicorn backend.main:app."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.retrieval.engine import HybridRetriever
from backend.retrieval.reranker import get_reranker
from backend.retrieval.semantic import get_embedding_model
from backend.storage.qdrant import get_client, load_chunks

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def initialize_retrieval():
    client = get_client()
    chunks = load_chunks(client)
    retriever = HybridRetriever(client, chunks)
    get_embedding_model()
    get_reranker()
    logger.info(
        "Retrieval ready: %d chunks, semantic/BM25 weights %.2f/%.2f",
        len(chunks),
        config.SEMANTIC_WEIGHT,
        1 - config.SEMANTIC_WEIGHT,
    )
    return retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.retriever = await run_in_threadpool(initialize_retrieval)
    try:
        yield
    finally:
        app.state.retriever = None
        get_client().close()
        get_client.cache_clear()


app = FastAPI(
    title="Document Atlas",
    description="RAG hybride : recherche sémantique + BM25",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/api/health")
def health(request: Request):
    retriever = getattr(request.app.state, "retriever", None)
    return {
        "status": "ok" if retriever else "initializing",
        "retrieval_ready": retriever is not None,
        "bm25_ready": retriever is not None,
        "indexed_chunks": len(retriever.keyword.hits) if retriever else 0,
        "semantic_weight": config.SEMANTIC_WEIGHT,
        "keyword_weight": 1 - config.SEMANTIC_WEIGHT,
        "graph_ready": retriever is not None and retriever.graph is not None,
    }


@app.get("/")
def root(request: Request):
    return {"message": "Document Atlas", "status": health(request)["status"]}

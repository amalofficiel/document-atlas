import logging

from fastapi import APIRouter, HTTPException, Request

from backend.services.answers import generate_answer
from backend.services.context import build_context

from .schemas import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    question = req.question.strip()
    if not question:
        raise HTTPException(
            status_code=400, detail="La question ne peut pas être vide."
        )
    retriever = getattr(request.app.state, "retriever", None)
    if retriever is None:
        raise HTTPException(
            status_code=503,
            detail="La recherche documentaire est en cours d’initialisation.",
        )
    try:
        results = retriever.search(question, top_k=req.top_k)
        context, sources = build_context(results)
    except Exception:
        logger.exception("Document retrieval failed")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la recherche dans les documents."
        ) from None
    try:
        answer = generate_answer(question, context)
    except Exception:
        logger.exception("Answer generation failed")
        raise HTTPException(
            status_code=503,
            detail="Le service de génération est indisponible. Veuillez réessayer.",
        ) from None
    return ChatResponse(answer=answer, sources=sources)

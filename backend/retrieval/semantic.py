"""Multilingual dense retrieval, with an optional exact-document filter."""

from functools import lru_cache

from qdrant_client.models import FieldCondition, Filter, MatchAny

from backend.config import COLLECTION_NAME

from .models import SearchHit


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    model.max_seq_length = 256
    return model


def search_semantic(
    client, question: str, top_k: int = 100, filenames: set[str] | None = None
) -> list[SearchHit]:
    if filenames is not None and not filenames:
        return []
    query_filter = (
        Filter(
            must=[FieldCondition(key="filename", match=MatchAny(any=sorted(filenames)))]
        )
        if filenames is not None
        else None
    )
    embedding = get_embedding_model().encode(
        question, normalize_embeddings=True, show_progress_bar=False
    )
    points = client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding.tolist(),
        query_filter=query_filter,
        limit=top_k,
    ).points
    return [
        SearchHit(
            id=str(point.id), payload=point.payload or {}, score=float(point.score)
        )
        for point in points
    ]

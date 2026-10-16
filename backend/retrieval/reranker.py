from __future__ import annotations

import re
from functools import lru_cache

MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


@lru_cache(maxsize=1)
def get_reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(MODEL_NAME)


def rerank_results(question: str, results: list, top_k: int = 3):
    if not results:
        return []

    pairs = []

    for result in results:
        payload = result.payload or {}
        filename = payload.get("filename") or ""
        text = payload.get("text") or ""

        metadata = f"Document : {filename}"

        match = re.search(r"Cir_(\d{4})_(\d+)", filename, flags=re.IGNORECASE)
        if match:
            year, number = match.groups()
            metadata += f"\nCirculaire n°{year}-{number}"

        passage = f"{metadata}\nPage : {payload.get('page')}\n{text}"
        pairs.append((question, passage))

    scores = get_reranker().predict(pairs, show_progress_bar=False)

    ranked = [
        {"result": result, "rerank_score": float(score)}
        for result, score in zip(results, scores)
    ]
    ranked.sort(key=lambda item: item["rerank_score"], reverse=True)

    return ranked[:top_k]

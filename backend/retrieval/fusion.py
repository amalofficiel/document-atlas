"""Weighted reciprocal rank fusion; no raw BM25/cosine score mixing."""

from dataclasses import replace

from .models import SearchHit


def fuse_ranked(
    semantic: list[SearchHit],
    keyword: list[SearchHit],
    semantic_weight: float = 0.5,
    rank_constant: int = 60,
) -> list[SearchHit]:
    if not 0 <= semantic_weight <= 1 or rank_constant < 1:
        raise ValueError("Invalid RRF weights or rank constant.")
    merged = {}
    for name, hits, weight in [
        ("semantic", semantic, semantic_weight),
        ("bm25", keyword, 1 - semantic_weight),
    ]:
        if weight == 0:
            continue
        seen = set()
        for rank, hit in enumerate(hits, start=1):
            if hit.id in seen:
                continue
            seen.add(hit.id)
            previous = merged.get(hit.id, replace(hit, score=0.0, scores={}, ranks={}))
            merged[hit.id] = replace(
                previous,
                score=previous.score + weight / (rank_constant + rank),
                scores={**previous.scores, name: hit.score},
                ranks={**previous.ranks, name: rank},
            )
    return sorted(merged.values(), key=lambda hit: (-hit.score, hit.id))

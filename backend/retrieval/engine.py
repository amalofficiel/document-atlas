"""Semantic + BM25 retrieval, rank fusion, then multilingual reranking."""

import logging

from backend import config

from .fusion import fuse_ranked
from .keyword import BM25Index
from .models import SearchHit
from .references import extract_circular_reference, matches_circular
from .reranker import rerank_results
from .semantic import search_semantic

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(
        self,
        client,
        chunks: list[SearchHit],
        semantic_weight: float = config.SEMANTIC_WEIGHT,
    ):
        self.client = client
        self.keyword = BM25Index(chunks)
        self.semantic_weight = semantic_weight
        self.graph = None
        if config.USE_GRAPH_RAG:
            from .graph.builder import build_graph

            self.graph = build_graph([hit.payload for hit in chunks])

    def candidates(self, question: str, candidate_k: int = config.CANDIDATE_K) -> dict:
        reference = extract_circular_reference(question)
        filenames = (
            {
                hit.payload["filename"]
                for hit in self.keyword.hits
                if matches_circular(hit.payload["filename"], reference)
            }
            if reference
            else None
        )
        semantic = search_semantic(self.client, question, candidate_k, filenames)
        keyword = self.keyword.search(question, candidate_k, filenames)
        fused = fuse_ranked(semantic, keyword, self.semantic_weight, config.RRF_K)[
            :candidate_k
        ]
        logger.info(
            "Hybrid candidates: semantic=%d BM25=%d fused=%d weights=%.2f/%.2f",
            len(semantic),
            len(keyword),
            len(fused),
            self.semantic_weight,
            1 - self.semantic_weight,
        )
        return {"semantic": semantic, "bm25": keyword, "fused": fused}

    def search(self, question: str, top_k: int = 3) -> list[dict]:
        candidates = self.candidates(question)["fused"]
        results = self._rerank(question, candidates, top_k, "hybrid")
        # Optional legacy graph fallback; never bypasses relevance reranking.
        if not results and self.graph is not None:
            from .graph.search import search_graph

            graph_hits = [
                SearchHit(item["node"], item, item["score"])
                for item in search_graph(question, self.graph, top_k=config.CANDIDATE_K)
            ]
            results = self._rerank(question, graph_hits, top_k, "graph")
        return results

    @staticmethod
    def _rerank(
        question: str, candidates: list[SearchHit], top_k: int, retrieval_type: str
    ) -> list[dict]:
        ranked = rerank_results(question, candidates, top_k=len(candidates))
        selected, seen_pages = [], set()
        for item in ranked:
            if (
                config.RERANK_THRESHOLD is not None
                and item["rerank_score"] < config.RERANK_THRESHOLD
            ):
                continue
            hit = item["result"]
            page_key = (hit.payload.get("filename"), hit.payload.get("page"))
            if page_key in seen_pages:
                continue
            seen_pages.add(page_key)
            selected.append(
                {
                    **hit.payload,
                    "retrieval_type": retrieval_type,
                    "fusion_score": hit.score,
                    "retrieval_scores": hit.scores,
                    "retrieval_ranks": hit.ranks,
                    "rerank_score": item["rerank_score"],
                }
            )
            if len(selected) >= top_k:
                break
        return selected

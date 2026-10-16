from __future__ import annotations

import math
import re

import networkx as nx

from ..references import (
    extract_circular_reference,
    matches_circular,
)

STOPWORDS = {
    "quel",
    "quelle",
    "quels",
    "quelles",
    "est",
    "sont",
    "dans",
    "pour",
    "avec",
    "une",
    "des",
    "les",
    "sur",
    "par",
    "de",
    "du",
    "la",
    "le",
    "un",
    "et",
    "ou",
    "en",
    "à",
    "au",
    "aux",
    "qui",
    "que",
    "comment",
    "combien",
    "où",
}


def _extract_question_words(question: str) -> set[str]:
    """Extrait les mots importants de la question."""
    words = re.findall(r"\b[\wÀ-ÿ]+\b", question.lower())

    return {word for word in words if len(word) >= 3 and word not in STOPWORDS}


def _variants(word: str) -> set[str]:
    """Ajoute une variante au singulier ou au pluriel."""
    variants = {word}

    if word.endswith(("s", "x")) and len(word) > 4:
        variants.add(word[:-1])
    else:
        variants.add(word + "s")

    return variants


def search_graph(
    question: str,
    graph: nx.Graph,
    top_k: int = 5,
) -> list[dict]:
    """Recherche des passages par les mots-clés du graphe."""
    if graph is None or graph.number_of_nodes() == 0:
        return []

    reference = extract_circular_reference(question)
    question_words = _extract_question_words(question)

    if not question_words:
        return []

    question_years = {int(year) for year in re.findall(r"\b(?:19|20)\d{2}\b", question)}

    chunk_scores: dict[str, float] = {}
    chunk_matches: dict[str, int] = {}
    words_found = 0

    for word in question_words:
        chunks_for_word: dict[str, float] = {}

        for variant in _variants(word):
            keyword_node = f"keyword::{variant}"

            if keyword_node not in graph:
                continue

            weight = 1.0 / math.log(2 + graph.degree(keyword_node))

            for neighbor in graph.neighbors(keyword_node):
                data = graph.nodes[neighbor]

                if data.get("type") != "chunk":
                    continue

                # Restreindre les candidats à la circulaire demandée.
                if reference is not None:
                    filename = data.get("filename") or ""
                    if not matches_circular(filename, reference):
                        continue

                chunks_for_word[neighbor] = max(
                    chunks_for_word.get(neighbor, 0.0),
                    weight,
                )

        if not chunks_for_word:
            continue

        words_found += 1

        for chunk_node, weight in chunks_for_word.items():
            chunk_scores[chunk_node] = chunk_scores.get(chunk_node, 0.0) + weight
            chunk_matches[chunk_node] = chunk_matches.get(chunk_node, 0) + 1

    if words_found == 0:
        return []

    min_matches = min(2, words_found)
    results = []

    for chunk_node, score in chunk_scores.items():
        if chunk_matches[chunk_node] < min_matches:
            continue

        data = graph.nodes[chunk_node]
        text = (data.get("text") or "").strip()

        if not text:
            continue

        if question_years and data.get("year") in question_years:
            score *= 1.5

        results.append(
            {
                "text": text,
                "filename": data.get("filename", ""),
                "page": data.get("page"),
                "year": data.get("year"),
                "chunk_id": data.get("chunk_id"),
                "score": float(score),
                "node": chunk_node,
                "retrieval_type": "graph",
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]

from __future__ import annotations

import hashlib
import re

import networkx as nx

STOPWORDS = {
    "dans",
    "avec",
    "pour",
    "sans",
    "cette",
    "comme",
    "mais",
    "plus",
    "être",
    "sont",
    "une",
    "des",
    "les",
    "aux",
    "sur",
    "par",
    "est",
    "qui",
    "que",
    "dont",
    "leur",
    "leurs",
    "entre",
    "ainsi",
    "elle",
    "elles",
    "nous",
    "vous",
    "ils",
    "avoir",
    "fait",
    "faire",
    "selon",
    "tous",
    "toutes",
}


def _extract_keywords(text: str, min_length: int = 4) -> list[str]:
    """Extrait des mots simples pouvant servir de mots-clés dans le graphe."""

    words = re.findall(r"\b[\wÀ-ÿ]+\b", text.lower())

    keywords = {
        word for word in words if len(word) >= min_length and word not in STOPWORDS
    }

    return sorted(keywords)


def build_graph(records: list[dict]) -> nx.Graph:
    """
    Construit le graphe de connaissances à partir des chunks.

    Structure :
        Document --contains--> Chunk --has_keyword--> Keyword
    """

    graph = nx.Graph()

    for record in records:
        filename = record["filename"]
        year = record.get("year")
        text = record["text"]

        # 1. Nœud document
        graph.add_node(filename, type="document", year=year)

        # 2. Nœud chunk (on garde la page et l'identifiant d'origine,
        #    pour que les sources du GraphRAG affichent la page)
        chunk_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        chunk_node = f"{filename}_{chunk_hash}"

        graph.add_node(
            chunk_node,
            type="chunk",
            text=text,
            filename=filename,
            year=year,
            page=record.get("page"),
            chunk_id=record.get("chunk_id"),
        )

        # 3. Document -> Chunk
        graph.add_edge(filename, chunk_node, relation="contains")

        # 4. Chunk -> Mots-clés
        for keyword in _extract_keywords(text):
            keyword_node = f"keyword::{keyword}"

            graph.add_node(keyword_node, type="keyword", value=keyword)
            graph.add_edge(chunk_node, keyword_node, relation="has_keyword")

    return graph

"""In-memory BM25 over the same chunks stored in Qdrant.

Uses Lucene-style positive IDF: log(1 + (N - df + .5) / (df + .5)).
The index is built once at startup, not rebuilt for each request.
"""

import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import replace

import numpy as np

from .models import SearchHit

STOPWORDS = set(
    """le la les de du des un une et ou en dans pour par sur au aux ce ces cette est sont quelle quelles quel quels comment que qui a à the a an of in on for to and or is are what which how
ما هي هو من في على عن الى إلى و أو التي الذي هذا هذه هل كيف شروط""".split()
) - {"شروط"}
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ـ": ""})


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize(
        "NFKD", text.translate(DIGITS).translate(ARABIC).casefold()
    )
    text = "".join(c for c in text if not unicodedata.combining(c))
    tokens = []
    for token in re.findall(r"[^\W_]+", text, re.UNICODE):
        if token in STOPWORDS or len(token) < 2:
            continue
        if token.startswith("ال") and len(token) > 4:
            token = token[2:]
        elif (
            token.isascii()
            and token.isalpha()
            and token.endswith(("s", "x"))
            and len(token) > 4
        ):
            token = token[:-1]
        tokens.append(token)
    return tokens


def document_text(payload: dict) -> str:
    filename = payload.get("filename", "")
    kind = "circulaire منشور" if filename.lower().startswith("cir_") else "note مذكرة"
    return f"{filename} {kind} {payload.get('text', '')}"


class BM25Index:
    def __init__(self, hits: list[SearchHit], k1: float = 1.5, b: float = 0.75):
        self.hits = hits
        self.k1, self.b = k1, b
        tokens = [tokenize(document_text(hit.payload)) for hit in hits]
        self.lengths = np.array([len(t) for t in tokens], dtype=float)
        self.average_length = float(self.lengths.mean()) if len(tokens) else 1.0
        postings = defaultdict(list)
        for index, terms in enumerate(tokens):
            for term, frequency in Counter(terms).items():
                postings[term].append((index, frequency))
        self.postings = {
            term: (
                np.array([i for i, _ in items]),
                np.array([f for _, f in items], dtype=float),
            )
            for term, items in postings.items()
        }

    def search(
        self, question: str, top_k: int = 100, filenames: set[str] | None = None
    ) -> list[SearchHit]:
        if not self.hits or top_k < 1:
            return []
        scores = np.zeros(len(self.hits))
        for term in set(tokenize(question)):
            posting = self.postings.get(term)
            if posting is None:
                continue
            indices, frequencies = posting
            idf = math.log1p(
                (len(self.hits) - len(indices) + 0.5) / (len(indices) + 0.5)
            )
            norm = self.k1 * (
                1
                - self.b
                + self.b * self.lengths[indices] / max(self.average_length, 1.0)
            )
            scores[indices] += idf * frequencies * (self.k1 + 1) / (frequencies + norm)
        matches = [
            i
            for i, score in enumerate(scores)
            if score > 0
            and (filenames is None or self.hits[i].payload["filename"] in filenames)
        ]
        matches.sort(key=lambda i: (-scores[i], self.hits[i].id))
        return [replace(self.hits[i], score=float(scores[i])) for i in matches[:top_k]]

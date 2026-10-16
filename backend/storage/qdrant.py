from __future__ import annotations

import hashlib
import re
import uuid
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from backend.config import COLLECTION_NAME, QDRANT_DIR


# Qdrant est stocké localement dans le projet
@lru_cache(maxsize=1)
def get_client():
    QDRANT_DIR.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_DIR))


# Espace de noms fixe pour fabriquer des identifiants stables
_NAMESPACE = uuid.UUID("6f1d2b1e-5a43-4c52-9d2e-0b7a4f3c9a11")

BATCH_SIZE = 128


def _extract_year(filename: str):
    """Extrait une année du nom du fichier (ex. Cir_2018_12_fr.pdf -> 2018)."""
    match = re.search(r"(?:19|20)\d{2}", filename)
    return int(match.group()) if match else None


def _point_id(chunk: dict) -> str:
    """
    Identifiant stable pour un chunk : le même chunk donne toujours le même
    identifiant, donc relancer l'indexation ne crée pas de doublons et
    n'écrase jamais un autre document.
    """
    text_hash = hashlib.sha1(chunk["text"].encode("utf-8")).hexdigest()
    key = f"{chunk['filename']}|{chunk['page']}|{chunk['chunk_id']}|{text_hash}"
    return str(uuid.uuid5(_NAMESPACE, key))


def create_collection(vector_size: int = 384):
    """Crée la collection Qdrant si elle n'existe pas."""

    client = get_client()
    collections = client.get_collections().collections

    exists = any(collection.name == COLLECTION_NAME for collection in collections)

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        print(f"Collection créée : {COLLECTION_NAME}")
    else:
        print(f"Collection déjà existante : {COLLECTION_NAME}")


def insert_chunks(chunks, embeddings):
    """Insère les chunks, embeddings et métadonnées dans Qdrant."""

    client = get_client()
    points = []

    for chunk, embedding in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=_point_id(chunk),
                vector=embedding.tolist(),
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "filename": chunk["filename"],
                    "page": chunk["page"],
                    "text": chunk["text"],
                    "year": chunk.get("year") or _extract_year(chunk["filename"]),
                },
            )
        )

    for start in range(0, len(points), BATCH_SIZE):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[start : start + BATCH_SIZE],
        )

    print(f"{len(points)} chunks insérés dans Qdrant.")


def load_chunks(client) -> list:
    """Load payloads once; BM25 and vectors must share the same IDs/corpus."""
    from backend.retrieval.models import SearchHit

    if not client.collection_exists(COLLECTION_NAME):
        raise RuntimeError(
            "Index Qdrant absent. Exécutez python -m scripts.index_documents."
        )
    chunks, offset = [], None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        chunks.extend(
            SearchHit(str(point.id), point.payload)
            for point in points
            if point.payload
            and point.payload.get("text")
            and point.payload.get("filename")
            and point.payload.get("page")
        )
        if offset is None:
            break
    if not chunks:
        raise RuntimeError(
            "Index Qdrant vide. Exécutez python -m scripts.index_documents."
        )
    return chunks

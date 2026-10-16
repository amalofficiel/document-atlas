from __future__ import annotations

import argparse

from backend.config import DOCUMENTS_DIR
from backend.ingestion.pdf import chunk_pdf
from backend.retrieval.semantic import get_embedding_model
from backend.storage.qdrant import (
    COLLECTION_NAME,
    create_collection,
    get_client,
    insert_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Indexe les PDF du dossier documents/ dans Qdrant."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Supprime la collection existante avant d'indexer.",
    )
    args = parser.parse_args()
    client = get_client()
    model = get_embedding_model()

    if args.reset:
        names = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME in names:
            client.delete_collection(COLLECTION_NAME)
            print(f"Collection supprimée : {COLLECTION_NAME}")

    if not args.reset and client.collection_exists(COLLECTION_NAME):
        if client.count(COLLECTION_NAME).count:
            raise SystemExit(
                "Index existant : arrêtez le backend, puis utilisez --reset pour le reconstruire."
            )

    create_collection(vector_size=model.get_embedding_dimension())

    pdf_files = sorted(DOCUMENTS_DIR.rglob("*.pdf"))

    if not pdf_files:
        raise SystemExit(f"Aucun PDF trouvé dans {DOCUMENTS_DIR}")

    print(f"{len(pdf_files)} PDF trouvés")

    all_chunks = []

    for pdf in pdf_files:
        try:
            chunks = chunk_pdf(pdf)
        except Exception as error:
            print(f"PDF ignoré (illisible) : {pdf.name} ({error})")
            continue

        if not chunks:
            print(f"Aucun texte dans {pdf.name} (PDF scanné ?)")
            continue

        print(f"{pdf.name} : {len(chunks)} chunks")
        all_chunks.extend(chunks)

    if not all_chunks:
        raise SystemExit("Aucun chunk à indexer.")

    embeddings = model.encode(
        [chunk["text"] for chunk in all_chunks],
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True,
    )

    insert_chunks(all_chunks, embeddings)

    print(f"Terminé : {len(all_chunks)} chunks indexés.")


if __name__ == "__main__":
    try:
        main()
    finally:
        get_client().close()
        get_client.cache_clear()

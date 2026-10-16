"""Evaluate page retrieval without LLM calls or paid APIs.

Input accepts the schema used by evaluation_queries_enriched.json.
Only answerable rows enter ranking metrics; negatives are retained as diagnostics.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import statistics
import time
from collections import defaultdict
from pathlib import Path


def page_keys(hits, k):
    keys = []
    for hit in hits:
        payload = hit.payload if hasattr(hit, 'payload') else hit
        key = (payload['filename'], payload['page'])
        if key not in keys:
            keys.append(key)
        if len(keys) >= k:
            break
    return keys


def ranking_metrics(keys, expected, k):
    """One labeled relevant page: hit@k equals recall@k for this schema."""
    selected = list(dict.fromkeys(keys))[:k]
    rank = selected.index(expected) + 1 if expected in selected else None
    return {'hit_at_k': float(rank is not None),
            'mrr_at_k': 1.0 / rank if rank else 0.0}


def load_queries(path, corpus_pages):
    rows = json.loads(path.read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError('Queries must be a nonempty JSON list.')
    seen = set()
    for row in rows:
        if not isinstance(row.get('id'), str) or row['id'] in seen:
            raise ValueError('Every query requires a unique string id.')
        seen.add(row['id'])
        if not isinstance(row.get('query'), str) or not row['query'].strip():
            raise ValueError(f"Empty query: {row['id']}")
        answerable = row.get('relevant', True) is not False and row.get('expected_behavior', 'answer') == 'answer'
        row['_answerable'] = answerable
        if answerable and (row.get('expected_source'), row.get('expected_page')) not in corpus_pages:
            raise ValueError(f"Labeled source/page absent from index: {row['id']}")
    if not any(row['_answerable'] for row in rows):
        raise ValueError('No answerable rows to evaluate.')
    return rows


def main():
    from backend import config
    from backend.retrieval.engine import HybridRetriever
    from backend.retrieval.fusion import fuse_ranked
    from backend.retrieval.references import extract_circular_reference, matches_circular
    from backend.retrieval.reranker import get_reranker, MODEL_NAME
    from backend.retrieval.semantic import get_embedding_model, search_semantic
    from backend.storage.qdrant import get_client, load_chunks

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queries', type=Path, default=Path('evaluation/queries.json'))
    parser.add_argument('--output', type=Path, default=Path('evaluation/results.json'))
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--candidate-k', type=int, default=8)
    parser.add_argument('--no-rerank', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.top_k <= args.candidate_k:
        parser.error('Require 1 <= top-k <= candidate-k.')
    client = get_client()
    try:
        chunks = load_chunks(client)
        retriever = HybridRetriever(client, chunks)
        rows = load_queries(args.queries, {(h.payload['filename'], h.payload['page']) for h in chunks})
        # Warm up both models before measuring per-query retrieval latency.
        get_embedding_model().encode('warmup', normalize_embeddings=True, show_progress_bar=False)
        if not args.no_rerank:
            get_reranker().predict([('warmup','warmup')], show_progress_bar=False)
        records = []
        for i, row in enumerate(rows, 1):
            ref = extract_circular_reference(row['query'])
            filenames = {h.payload['filename'] for h in chunks if matches_circular(h.payload['filename'], ref)} if ref else None
            start = time.perf_counter()
            semantic = search_semantic(client, row['query'], args.candidate_k, filenames)
            semantic_ms = (time.perf_counter()-start)*1000
            start = time.perf_counter()
            bm25 = retriever.keyword.search(row['query'], args.candidate_k, filenames)
            bm25_ms = (time.perf_counter()-start)*1000
            start = time.perf_counter()
            hybrid = fuse_ranked(semantic,bm25,config.SEMANTIC_WEIGHT,config.RRF_K)[:args.candidate_k]
            hybrid_ms = semantic_ms + bm25_ms + (time.perf_counter()-start)*1000
            methods = {'semantic':(semantic,semantic_ms),'bm25':(bm25,bm25_ms),'hybrid':(hybrid,hybrid_ms)}
            for method,(hits,ms) in methods.items():
                variants = [(method, page_keys(hits,args.top_k), ms)]
                if not args.no_rerank:
                    start = time.perf_counter()
                    ranked = retriever._rerank(row['query'],hits,args.top_k,method)
                    variants.append((method+'_reranked',page_keys(ranked,args.top_k),ms+(time.perf_counter()-start)*1000))
                for name,keys,elapsed in variants:
                    record = {'id':row['id'],'language':row.get('language','unknown'),'method':name,'answerable':row['_answerable'],'latency_ms':round(elapsed,3),'retrieved_pages':[{'filename':fn,'page':pg} for fn,pg in keys]}
                    if row['_answerable']:
                        record.update(ranking_metrics(keys,(row['expected_source'],row['expected_page']),args.top_k))
                    records.append(record)
            print(f"[{i}/{len(rows)}] {row['id']}",flush=True)
        grouped = defaultdict(list)
        for r in records:
            if r['answerable']:
                grouped[(r['method'],'all')].append(r)
                grouped[(r['method'],r['language'])].append(r)
        summary = []
        for (method,lang),items in sorted(grouped.items()):
            latencies = sorted(r['latency_ms'] for r in items)
            summary.append({'method':method,'language':lang,'queries':len(items),'hit_at_k':round(statistics.mean(r['hit_at_k'] for r in items),4),'mrr_at_k':round(statistics.mean(r['mrr_at_k'] for r in items),4),'median_latency_ms':round(statistics.median(latencies),3)})
        corpus = sorted((h.id,h.payload) for h in chunks)
        result={'metadata':{'queries_sha256':hashlib.sha256(args.queries.read_bytes()).hexdigest(),'indexed_chunks_sha256':hashlib.sha256(json.dumps(corpus,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'indexed_chunks':len(chunks),'answerable_queries':sum(r['_answerable'] for r in rows),'negative_queries':sum(not r['_answerable'] for r in rows),'top_k':args.top_k,'candidate_k':args.candidate_k,'semantic_weight':config.SEMANTIC_WEIGHT,'rrf_k':config.RRF_K,'rerank_threshold':config.RERANK_THRESHOLD,'embedding_model':'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2','reranker':None if args.no_rerank else MODEL_NAME,'python':platform.python_version(),'platform':platform.platform(),'packages':{name:importlib.metadata.version(name) for name in ['numpy','qdrant-client','sentence-transformers','torch']},'generation_evaluated':False,'latency_note':'Warm models; sequential local measurements, no LLM. Reranked timings include the respective branch cost. Negatives excluded from ranking metrics.'},'summary':summary,'records':records}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(f'Saved {args.output}')
    finally:
        client.close()
        get_client.cache_clear()


if __name__ == '__main__':
    main()

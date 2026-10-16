# Retrieval evaluation report

Measured on 16 October 2026. No Groq calls were made.

## Protocol

- 6 fictional PDFs, 12 pages and 12 indexed passages.
- 24 answerable questions: 12 French and 12 Arabic, targeting French documents.
- 4 out-of-scope questions retained as diagnostics and excluded from ranking metrics.
- `top_k=3`, `candidate_k=8`, semantic weight `0.5`, RRF constant `60`.
- Cross-encoder reranking is applied to each baseline separately.
- Models are warmed before per-query latency measurements; cold start and index construction are excluded.

## Overall results

| Method | Hit@3 | MRR@3 | Median retrieval latency (ms) |
| --- | ---: | ---: | ---: |
| bm25 | 0.5417 | 0.5208 | 0.071 |
| bm25_reranked | 0.5417 | 0.5417 | 25.822 |
| hybrid | 0.9583 | 0.9097 | 14.631 |
| hybrid_reranked | 1.0000 | 1.0000 | 56.628 |
| semantic | 0.9583 | 0.8889 | 14.526 |
| semantic_reranked | 1.0000 | 1.0000 | 59.275 |

Hit@3 is the proportion of answerable questions whose labeled source page appears in the top three distinct pages. Each question has one labeled relevant page, so this also equals recall@3 for this dataset. MRR@3 averages the reciprocal rank of that page, with zero when absent.

## Language breakdown

| Method | Language | Questions | Hit@3 | MRR@3 |
| --- | --- | ---: | ---: | ---: |
| bm25 | ar | 12 | 0.0833 | 0.0833 |
| bm25 | fr | 12 | 1.0000 | 0.9583 |
| bm25_reranked | ar | 12 | 0.0833 | 0.0833 |
| bm25_reranked | fr | 12 | 1.0000 | 1.0000 |
| hybrid | ar | 12 | 0.9167 | 0.8194 |
| hybrid | fr | 12 | 1.0000 | 1.0000 |
| hybrid_reranked | ar | 12 | 1.0000 | 1.0000 |
| hybrid_reranked | fr | 12 | 1.0000 | 1.0000 |
| semantic | ar | 12 | 0.9167 | 0.8194 |
| semantic | fr | 12 | 1.0000 | 0.9583 |
| semantic_reranked | ar | 12 | 1.0000 | 1.0000 |
| semantic_reranked | fr | 12 | 1.0000 | 1.0000 |

## What the results show

BM25 retrieves the labeled page for all twelve French questions, but only one Arabic question, which includes the shared Latin identifier `P1`. The corpus is French: lexical matching alone has little cross-language coverage.

The raw semantic and hybrid branches both miss the archive-retention page for `archives_1_ar` in their top three. Their returned pages concern backups and token validity, showing a confusion between related duration/retention topics. Reranking recovers the labeled page from the candidate set.

Both semantic+reranker and hybrid+reranker reach the same perfect ranking on this small dataset. **This run does not demonstrate that hybrid retrieval outperforms semantic retrieval after reranking.** The six-method comparison is retained rather than reporting only the best score.

## Limits

The documents and questions were authored together. There is no independent held-out test set, no domain-expert annotation and no confidence interval. The corpus is tiny; the candidate budget covers much of it, making reranked scores easy to saturate. Results must not be generalized to the private BCT corpus or production traffic.

The evaluation measures retrieval only. It does not measure generated answer correctness, hallucination, citation entailment, legal validity or conversational behavior. Source-page ground truth is simplified: other useful but unlabeled pages are not counted as relevant.

Out-of-scope rows show what each retriever returns, but there is no calibrated abstention mechanism. Returning some pages for these questions must not be interpreted as a supported answer. No abstention accuracy is claimed.

Latency is measured sequentially on a single local machine with warm models. Values are descriptive, not deployment SLAs; model loading, network and Groq generation latency are excluded.

## Reproduce

```bash
python -m scripts.index_documents  # first run only, backend stopped
python -m scripts.evaluate_retrieval
```

The committed [raw results](results.json) include per-query rankings, timings, dataset/index hashes and measured package versions. [Queries](queries.json) and [authored corpus](corpus.json) are included. Missing labeled pages fail validation.

The runner also accepts the schema of `evaluation_queries_enriched.json` through `--queries`; use it only against the corresponding local index and keep private results outside the public repository.

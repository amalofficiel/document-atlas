import json
import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_retrieval import ranking_metrics, page_keys, load_queries
from backend.retrieval.models import SearchHit
from backend.retrieval.fusion import fuse_ranked
from backend.retrieval.keyword import BM25Index


class EvaluationTests(unittest.TestCase):
    def test_metrics_use_rank_and_cutoff(self):
        self.assertEqual(ranking_metrics([('x',1),('y',2)],('y',2),3),{'hit_at_k':1.0,'mrr_at_k':0.5})
        self.assertEqual(ranking_metrics([('x',1),('y',2)],('y',2),1),{'hit_at_k':0.0,'mrr_at_k':0.0})

    def test_duplicate_chunks_do_not_inflate_page_rank(self):
        hits=[SearchHit(str(i),{'filename':fn,'page':pg}) for i,(fn,pg) in enumerate([('x',1),('x',1),('y',2)])]
        self.assertEqual(page_keys(hits,3),[('x',1),('y',2)])

    def test_missing_label_fails_instead_of_improving_score(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'queries.json'
            p.write_text(json.dumps([{'id':'x','query':'q','expected_source':'missing.pdf','expected_page':1}]))
            with self.assertRaisesRegex(ValueError,'absent'):
                load_queries(p,{('exists.pdf',1)})

    def test_negative_rows_are_not_ranking_ground_truth(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'queries.json'
            p.write_text(json.dumps([{'id':'yes','query':'q','expected_source':'x','expected_page':1},{'id':'no','query':'q','relevant':False,'expected_behavior':'abstain'}]))
            rows=load_queries(p,{('x',1)})
            self.assertEqual([r['_answerable'] for r in rows],[True,False])

    def test_fusion_respects_single_branch_endpoints(self):
        a=SearchHit('a',{});b=SearchHit('b',{})
        self.assertEqual([h.id for h in fuse_ranked([a,b],[b,a],1)],['a','b'])
        self.assertEqual([h.id for h in fuse_ranked([a,b],[b,a],0)],['b','a'])

    def test_keyword_filter_prevents_cross_document_leakage(self):
        hits=[SearchHit('a',{'filename':'a.pdf','page':1,'text':'archive export'}),SearchHit('b',{'filename':'b.pdf','page':1,'text':'archive export'})]
        self.assertEqual([h.id for h in BM25Index(hits).search('archive',filenames={'b.pdf'})],['b'])


if __name__ == '__main__':
    unittest.main()

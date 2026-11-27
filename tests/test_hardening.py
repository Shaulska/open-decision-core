import unittest, tempfile
from pathlib import Path
from odc import audit, replay, verify, split_check
from odc.core import timestamp, MAX_DEPTH, MAX_EVIDENCE
from odc.__main__ import load
from test_core import fixture
import test_core

class HardeningTests(unittest.TestCase):
    def test_explicit_seconds(self):
        for value in ('2026-01-01T12:00Z','20260101T120000Z','2026-01-01T12:00:00-00:00','2026-01-01T12:00:00+00:60','2026-01-01T12:00:00.1234567Z'):
            with self.subTest(value=value), self.assertRaises(ValueError): timestamp(value)
    def test_missing_lineage(self):
        b=fixture(); del b['evidence'][0]['parents']; self.assertEqual(audit(b)['status'],'UNVERIFIED')
    def test_duplicate_parents(self):
        b=fixture(); b['evidence'][0]['parents']=['a','a']; self.assertEqual(audit(b)['status'],'BLOCK')
    def test_bad_id_replay(self):
        b=fixture(); b['evidence'].append({'id':[]}); self.assertEqual(replay(b,'d')['receipt']['status'],'BLOCK')
    def test_deep_lineage(self):
        b=fixture(); root=b['evidence'][0]; root['parents']=['1']
        for n in range(1,MAX_DEPTH+2): b['evidence'].append(dict(root,id=str(n),version=str(n+1),parents=[str(n+1)] if n<=MAX_DEPTH else []))
        with self.assertRaisesRegex(ValueError,'traversal limit'): audit(b)
    def test_size_bound(self):
        b=fixture(); b['evidence']*=MAX_EVIDENCE+1
        with self.assertRaisesRegex(ValueError,'limit'): audit(b)
    def test_nonfinite_exponent(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{"value":1e999}')
            with self.assertRaises(ValueError): load(p)
    def test_typed_receipt(self):
        b=fixture(); r=audit(b); r['decisions']=True; self.assertFalse(verify(b,r))
    def test_preserve_known_block(self):
        m=test_core.SplitTests().fixture(); m['test'][0]['id']='a'; del m['train'][0]['label_available_at']; self.assertEqual(split_check(m)['status'],'BLOCK')
    def test_provider_minute_interval(self):
        b=fixture(); r=b['evidence'][0]; r.update(precision='MINUTE',availability_kind='PROVIDER_PUBLISHED',received_at=None,available_at=r['published_at']); b['decisions'][0]['mode']='PROVIDER_ASOF'
        for stamp,status in [('2026-01-01T10:00:59Z','BLOCK'),('2026-01-01T10:01:00Z','UNVERIFIED'),('2026-01-01T10:01:59Z','UNVERIFIED'),('2026-01-01T10:02:00Z','PASS')]:
            b['decisions'][0]['decision_at']=stamp; self.assertEqual(audit(b)['status'],status)
    def test_minute_bad_boundary(self):
        b=fixture();r=b['evidence'][0];r.update(precision='MINUTE',availability_kind='PROVIDER_PUBLISHED',received_at=None,published_at='2026-01-01T10:01:01Z',available_at='2026-01-01T10:01:01Z');b['decisions'][0]['mode']='PROVIDER_ASOF';self.assertEqual(audit(b)['status'],'BLOCK')
    def test_incomplete_does_not_hide_later_violation(self):
        m=test_core.SplitTests().fixture(); m['train'].insert(0,{});m['train'][1]['label_available_at']='2026-01-04T00:00:00Z';r=split_check(m);self.assertEqual(r['status'],'BLOCK');self.assertIn('LATE_TRAIN_LABEL',r['issues'])

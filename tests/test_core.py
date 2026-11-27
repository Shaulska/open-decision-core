import copy, json, unittest, random, tempfile, subprocess, sys
from pathlib import Path
from odc import audit, replay, verify, split_check
from odc.__main__ import html_report, load

def fixture():
    return {'schema_version':1,'evidence':[{'id':'a','source':'demo','entity':'service','feature':'load','version':'1','value':42,'event_time':'2026-01-01T10:00:00Z','published_at':'2026-01-01T10:01:00Z','received_at':'2026-01-01T10:02:00Z','available_at':'2026-01-01T10:03:00Z','precision':'SECOND','availability_kind':'OBSERVED','usage':'OBSERVATION','source_ref':'synthetic:telemetry','parents':[]}],'decisions':[{'id':'d','decision_at':'2026-01-01T12:00:00Z','evidence_ids':['a'],'mode':'OBSERVED_REPLAY'}]}

class AuditTests(unittest.TestCase):
    def check(self,b,code,status):
        r=audit(b); self.assertEqual(r['status'],status); self.assertIn(code,[f['code'] for f in r['findings']]); return r
    def test_clean(self): self.assertEqual(audit(fixture())['status'],'PASS')
    def test_equal(self):
        b=fixture(); b['evidence'][0]['available_at']=b['decisions'][0]['decision_at']; self.assertEqual(audit(b)['status'],'PASS')
    def test_late(self):
        b=fixture(); b['evidence'][0]['available_at']='2026-01-01T12:01:00Z'; self.check(b,'LATE_AVAILABLE_AT','BLOCK')
    def test_unknown(self):
        b=fixture(); b['evidence'][0]['available_at']=None; self.check(b,'UNKNOWN_AVAILABILITY','UNVERIFIED')
    def test_naive(self):
        b=fixture(); b['evidence'][0]['available_at']='2026-01-01T10:03:00'; self.check(b,'INVALID_AVAILABLE_AT','BLOCK')
    def test_offsets(self):
        b=fixture(); b['evidence'][0]['available_at']='2026-01-01T13:03:00+03:00'; self.assertEqual(audit(b)['status'],'PASS')
    def test_day_precision(self):
        b=fixture(); b['evidence'][0]['precision']='DAY'; self.check(b,'UNSUPPORTED_PRECISION','UNVERIFIED')
    def test_missing_parent(self):
        b=fixture(); b['evidence'][0]['parents']=['missing']; self.check(b,'MISSING_EVIDENCE','BLOCK')
    def test_late_parent(self):
        b=fixture(); p=dict(b['evidence'][0],id='parent',feature='raw',available_at='2026-01-01T13:00:00Z'); b['evidence'].append(p); b['evidence'][0]['parents']=['parent']; self.check(b,'LATE_AVAILABLE_AT','BLOCK')
    def test_derived_before_parent(self):
        b=fixture(); b['evidence'].append(dict(b['evidence'][0],id='parent',feature='raw',available_at='2026-01-01T11:00:00Z')); b['evidence'][0]['parents']=['parent']; self.check(b,'DERIVED_BEFORE_PARENT','BLOCK')
    def test_cycle(self):
        b=fixture(); b['evidence'][0]['parents']=['a']; self.check(b,'LINEAGE_CYCLE','BLOCK')
    def test_duplicate_conflict(self):
        b=fixture(); b['evidence'].append(dict(b['evidence'][0],value=0)); self.check(b,'CONFLICTING_ID','BLOCK')
    def test_duplicate_identical(self):
        b=fixture(); b['evidence'].append(copy.deepcopy(b['evidence'][0])); self.assertEqual(audit(b)['status'],'PASS')
    def test_duplicate_version(self):
        b=fixture(); b['evidence'].append(dict(b['evidence'][0],id='b')); self.check(b,'DUPLICATE_VERSION_KEY','BLOCK')
    def test_exact_revision(self):
        b=fixture(); b['evidence'].append(dict(b['evidence'][0],id='b',version='2',available_at='2026-01-02T10:00:00Z')); self.assertEqual(replay(b,'d')['evidence'][0]['id'],'a'); self.assertEqual(audit(b)['status'],'PASS'); b['decisions'][0]['evidence_ids']=['b']; self.check(b,'LATE_AVAILABLE_AT','BLOCK')
    def test_future_observation(self):
        b=fixture(); b['evidence'][0]['event_time']='2026-01-02T10:00:00Z'; self.check(b,'FUTURE_OBSERVATION','BLOCK')
    def test_schedule(self):
        b=fixture(); b['evidence'][0].update(event_time='2026-01-02T10:00:00Z',usage='SCHEDULED'); self.assertEqual(audit(b)['status'],'PASS')
    def test_bad_order(self):
        b=fixture(); b['evidence'][0]['available_at']='2026-01-01T10:00:00Z'; self.check(b,'TIME_ORDER_VIOLATION','BLOCK')
    def test_provider(self):
        b=fixture(); r=b['evidence'][0]; r.update(availability_kind='PROVIDER_PUBLISHED',received_at=None,available_at=r['published_at']); b['decisions'][0]['mode']='PROVIDER_ASOF'; self.assertEqual(audit(b)['status'],'PASS'); b['decisions'][0]['mode']='OBSERVED_REPLAY'; self.check(b,'NO_LOCAL_RECEIPT','UNVERIFIED')
    def test_tamper(self):
        b=fixture(); r=audit(b); self.assertTrue(verify(b,r)); self.assertEqual(r,audit(b)); b['evidence'][0]['value']=43; self.assertFalse(verify(b,r))
    def test_retro(self):
        b=fixture(); b['decisions'][0]['mode']='RETROSPECTIVE'; self.check(b,'DECISION_MODE_UNVERIFIED','UNVERIFIED')
    def test_no_decisions(self):
        b=fixture(); b['decisions']=[]; self.check(b,'NO_DECISIONS','UNVERIFIED')
    def test_html_escape(self):
        b=fixture(); b['decisions'][0]['id']='<script>alert(1)</script>'; b['evidence'][0]['available_at']=None; self.assertNotIn('<script>',html_report(audit(b)))
    def test_random_100(self):
        for seed in range(100):
            rng=random.Random(seed); b=fixture(); minute=rng.randint(0,59); late=rng.choice([True,False]); b['evidence'][0]['available_at']=f'2026-01-01T{13 if late else 11}:{minute:02d}:00Z'; self.assertEqual(audit(b)['status'],'BLOCK' if late else 'PASS',seed)
    def test_json_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.json'; p.write_text('{"id":1,"id":2}'); self.assertRaises(ValueError,load,p)
    def test_cli_exit(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'b.json'; b=fixture(); p.write_text(json.dumps(b)); self.assertEqual(subprocess.run([sys.executable,'-m','odc','audit',str(p)],capture_output=True).returncode,0); b['evidence'][0]['available_at']=None; p.write_text(json.dumps(b)); self.assertEqual(subprocess.run([sys.executable,'-m','odc','audit',str(p)],capture_output=True).returncode,3)

class SplitTests(unittest.TestCase):
    def fixture(self): return {'fit_at':'2026-01-02T00:00:00Z','test_start':'2026-01-03T00:00:00Z','embargo_seconds':3600,'train':[{'id':'a','group':'g1','sample_at':'2026-01-01T10:00:00Z','label_available_at':'2026-01-01T11:00:00Z'}],'test':[{'id':'b','group':'g2','sample_at':'2026-01-03T00:00:00Z'}]}
    def test_clean(self): self.assertEqual(split_check(self.fixture())['status'],'PASS')
    def test_overlap(self):
        m=self.fixture(); m['test'][0].update(id='a',group='g1'); self.assertEqual(split_check(m)['issues'],['SPLIT_GROUP_OVERLAP','SPLIT_ID_OVERLAP'])
    def test_late_label(self):
        m=self.fixture(); m['train'][0]['label_available_at']='2026-01-03T01:00:00Z'; self.assertIn('LATE_TRAIN_LABEL',split_check(m)['issues'])
    def test_embargo(self):
        m=self.fixture(); m['embargo_seconds']=200000; self.assertIn('EMBARGO_VIOLATION',split_check(m)['issues'])
    def test_unknown(self):
        m=self.fixture(); del m['fit_at']; self.assertEqual(split_check(m)['status'],'UNVERIFIED')

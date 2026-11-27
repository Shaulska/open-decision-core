import copy,json,unittest
from pathlib import Path
from odc.benchmark import build_results
from odc.demo import render
from odc import verify

FIXTURE=Path(__file__).resolve().parents[1]/'examples/bea/releases.json'

class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.fixture=json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.result=build_results(self.fixture)
    def test_all_expected(self):
        self.assertEqual(self.result['summary'],{'cases':24,'matched':24,'counts':{'PASS':12,'BLOCK':6,'UNVERIFIED':6}})
    def test_every_receipt(self):
        for c in self.result['cases']:
            self.assertTrue(verify({'schema_version':1,'evidence':self.result['records'],'decisions':[c['decision']]},c['receipt']))
    def test_equal_value_still_leaks(self):
        c=next(c for c in self.result['cases'] if c['id']=='2024-Q2:second:third:PROVIDER_ASOF')
        self.assertEqual(c['evidence']['value'],3.0)
        self.assertEqual(c['receipt']['status'],'BLOCK')
    def test_no_fabricated_receipt(self):
        for r in self.result['records']: self.assertIsNone(r['received_at'])
        for c in self.result['cases']:
            if c['mode']=='OBSERVED_REPLAY': self.assertEqual(c['receipt']['status'],'UNVERIFIED')
    def test_deterministic(self): self.assertEqual(self.result,build_results(self.fixture))
    def test_fixture_membership(self):
        f=copy.deepcopy(self.fixture);f['releases'].pop();self.assertRaises(ValueError,build_results,f)
    def test_html_payload(self):
        h=render(self.result);payload=h.split('<script type="application/json" id="data">',1)[1].split('</script>',1)[0]
        self.assertEqual(json.loads(payload),self.result)
    def test_script_escaping(self):
        r=copy.deepcopy(self.result);r['scope']='</script><script>alert(1)</script>';h=render(r)
        self.assertNotIn('<script>alert(1)</script>',h)
    def test_export_raw_record_numbers(self):
        h=render(self.result);raw=h.split('<script type="application/json" id="raw-records">',1)[1].split('</script>',1)[0]
        self.assertIn('"value":3.0',raw)
        self.assertEqual(json.loads(raw),self.result['records'])
        self.assertIn("el('raw-records').textContent",h)
    def test_checked_in_outputs(self):
        self.assertEqual(json.loads((FIXTURE.parent/'results.json').read_text()),self.result)
        self.assertEqual((FIXTURE.parent/'index.html').read_text(),render(self.result))

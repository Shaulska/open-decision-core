from pathlib import Path
import importlib.util
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('odc_site_build', ROOT / 'site/build.py')
site_build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site_build)

class SiteTests(unittest.TestCase):
    def test_reproducible_site(self):
        self.assertEqual(site_build.build(), (ROOT / 'site/index.html').read_text())

    def test_original_receipts_and_raw_records(self):
        demo = (ROOT / 'examples/bea/index.html').read_text()
        page = site_build.build()
        for key in ('data', 'raw-records'):
            pattern = rf'<script type="application/json" id="{key}">(.*?)</script>'
            self.assertEqual(re.search(pattern, demo, re.S).group(1), re.search(pattern, page, re.S).group(1))
        payload = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S).group(1))
        self.assertEqual(payload['summary']['matched'], 24)
        self.assertEqual(payload['summary']['cases'], 24)

    def test_roadmap_disclosed(self):
        page = site_build.build()
        self.assertIn('02 / ROADMAP', page)
        self.assertIn('03 / ROADMAP', page)
        self.assertIn('Not yet implemented', page)

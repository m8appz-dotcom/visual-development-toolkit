"""The public package must retain the source identity recorded in its evidence."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublishedDemoTests(unittest.TestCase):
    def test_packaged_bytes_match_the_recorded_source(self):
        folder = ROOT / 'docs/examples'
        evidence = json.loads((folder / 'evidence.json').read_text(encoding='utf-8'))
        packaged = (folder / 'packaged-project/index.html').read_bytes()
        self.assertEqual(hashlib.sha256(packaged).hexdigest(), evidence['sourceSha256'])
        self.assertTrue(evidence['originalUnchanged'])
        self.assertTrue(evidence['archiveContentMatchesOriginal'])


if __name__ == '__main__':
    unittest.main()

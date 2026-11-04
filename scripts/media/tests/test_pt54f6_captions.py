"""F6 caption overrides on G4 AI and Origin galleries, including CSRF protection."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pt54f2_prepare import Rejected
from pt54f5_library import current_library
from pt54f6_captions import load_captions, save_caption
from pt54f4_manager import MediaManagerServer

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / 'frontend/src/components/catalog'


class CaptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.root = Path(self.temp.name) / 'library'
        for sub in ('ingest-drop', 'staging', 'masters', 'receipts'):
            (self.root / sub).mkdir(parents=True)
        target = self.repo / 'frontend/src/components/catalog'
        target.mkdir(parents=True)
        for name in ('productMediaRegistry.ts', 'photoSetIndex.json'):
            shutil.copyfile(CATALOG / name, target / name)
        (target / 'photoCaptionOverrides.json').write_text(
            '{"schema_version":1,"families":{},"configurations":{}}\n', encoding='utf-8')
        (target / 'publishedPhotoIndex.json').write_text(
            '{"schema_version":1,"entries":[]}\n', encoding='utf-8')
        (self.repo / 'frontend/public/products/media').mkdir(parents=True)
        self.key = 'refine:1.5:neoprene'

    def photo(self, key, ident):
        row = next(r for r in current_library(self.repo) if r['key'] == key)
        return next(p for p in row['photos'] if p['id'] == ident)

    def test_preserves_default_labels_and_origin(self):
        self.assertEqual(self.photo(self.key, 'tank')['label'], 'Treatment tank')
        self.assertEqual(self.photo(self.key, 'brine')['label'], 'Brine tank · front')
        self.assertEqual(self.photo('origin:DD5RO', 'system')['label'], 'Complete five-stage system')
        self.assertEqual(self.photo('harmony:1.5:stainless:pass-through:2', 'pureline')['label'],
                         'Pureline assembly · front')

    def test_configuration_then_family_precedence_and_reset(self):
        _, etag = load_captions(self.repo)
        result = save_caption(self.repo, self.root, self.key, 'tank', 'family', 'Treatment vessel', etag)
        self.assertTrue(result['changed'])
        self.assertEqual(self.photo(self.key, 'tank')['label'], 'Treatment vessel')
        sibling = 'refine:2.0:stainless'
        self.assertEqual(self.photo(sibling, 'tank')['label'], 'Treatment vessel')
        result = save_caption(self.repo, self.root, self.key, 'tank', 'configuration', 'Media tank', result['etag'])
        self.assertEqual(self.photo(self.key, 'tank')['label'], 'Media tank')
        self.assertEqual(self.photo(sibling, 'tank')['label'], 'Treatment vessel')
        self.assertEqual(self.photo(self.key, 'tank')['caption_source'], 'configuration')
        result = save_caption(self.repo, self.root, self.key, 'tank', 'configuration', '', result['etag'])
        self.assertEqual(self.photo(self.key, 'tank')['label'], 'Treatment vessel')
        self.assertGreaterEqual(len(list((self.root / 'receipts/caption-backups').glob('*.json'))), 3)

    def test_rejects_invalid_and_stale_changes(self):
        _, etag = load_captions(self.repo)
        with self.assertRaises(Rejected):
            save_caption(self.repo, self.root, self.key, 'not-in-gallery', 'family', 'Oops', etag)
        for text in ('bad\nname', 'x' * 97, ' space', '<bad>\n'):
            with self.subTest(text=text), self.assertRaises(Rejected):
                save_caption(self.repo, self.root, self.key, 'system', 'configuration', text, etag)
        saved = save_caption(self.repo, self.root, self.key, 'system', 'configuration', 'Updated hero', etag)
        with self.assertRaisesRegex(Rejected, 'changed'):
            save_caption(self.repo, self.root, self.key, 'system', 'family', 'Stale edit', etag)
        self.assertEqual(self.photo(self.key, 'system')['label'], 'Updated hero')
        self.assertNotEqual(saved['etag'], etag)

    def test_local_server_csrf_and_actual_save(self):
        server = MediaManagerServer(('127.0.0.1', 0), self.repo, self.root)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f'http://127.0.0.1:{server.server_port}'

        def get(path):
            with urlopen(base + path) as response:
                return json.load(response)

        state = get('/api/state')
        library = get('/api/library')
        self.assertIn('caption_etag', library)
        payload = json.dumps({'key': self.key, 'photo_id': 'brine', 'scope': 'configuration',
                              'caption': 'Salt storage tank', 'expected_etag': library['caption_etag']}).encode()
        req = Request(base + '/api/caption', data=payload,
                      headers={'Content-Type': 'application/json'}, method='POST')
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 403)
        req = Request(base + '/api/caption', data=payload,
                      headers={'Content-Type': 'application/json',
                               'Origin': base, 'X-PT54-CSRF': state['csrf']}, method='POST')
        with urlopen(req) as response:
            out = json.load(response)
        self.assertTrue(out['changed'])
        self.assertEqual(get('/api/library')['configurations'][0]['family'], 'essence')
        self.assertEqual(self.photo(self.key, 'brine')['label'], 'Salt storage tank')


if __name__ == '__main__':
    unittest.main()

"""G4 library: approved AI placeholders + Origin, safe local-only previews."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import unittest
from urllib.request import urlopen
from urllib.error import HTTPError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pt54f5_library import current_library, library_image, selected_file
from pt54f2_prepare import Rejected
from pt54f4_manager import MediaManagerServer

REPO = Path(__file__).resolve().parents[3]
CATALOG = REPO / 'frontend/src/components/catalog'


class ExistingLibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        target = self.repo / 'frontend/src/components/catalog'
        target.mkdir(parents=True)
        for name in ('productMediaRegistry.ts', 'photoSetIndex.json'):
            shutil.copyfile(CATALOG / name, target / name)
        (target / 'publishedPhotoIndex.json').write_text('{"schema_version":1,"entries":[]}', encoding='utf-8')
        (target / 'photoCaptionOverrides.json').write_text(
            '{"schema_version":1,"families":{},"configurations":{}}', encoding='utf-8')
        index = json.loads((target / 'photoSetIndex.json').read_text())
        self.key = 'refine:1.5:neoprene'
        self.hero_url = index['sets']['ai-placeholder']['entries'][self.key][0]['media']['src']
        self.hero_path = self.repo / 'frontend/public' / self.hero_url.lstrip('/')
        self.hero_path.parent.mkdir(parents=True, exist_ok=True)
        self.hero_path.write_bytes(b'RIFF_current_ai_hero')

    def test_current_approved_configurations_and_origin(self):
        rows = current_library(self.repo)
        self.assertEqual(len(rows), 26)
        keys = {r['key'] for r in rows}
        self.assertIn('origin:DD5RO', keys)
        self.assertIn('origin:DD6ROAE', keys)
        self.assertIn(self.key, keys)
        self.assertIn('harmony:2.0:stainless:pass-through:3', keys)
        self.assertEqual(len(next(r for r in rows if r['key'] == 'origin:DD5RO')['photos']), 6)
        self.assertIn('brine', {p['id'] for p in next(r for r in rows if r['key'] == self.key)['photos']})
        self.assertTrue(all('archetype' not in key and 'realistic' not in key for key in keys))
        self.assertTrue(next(r for r in rows if r['key'] == self.key)['photos'][0]['available'])

    def test_preview_only_authorized_assets(self):
        self.assertEqual(selected_file(self.repo, self.hero_url), self.hero_path)
        for path in ('/etc/passwd', '/products/media/../secret.png', '/products/media/.hidden.webp',
                     '/products/media/ai-placeholders/../../unsafe.webp', '/products/media/refine/fake.svg'):
            with self.subTest(path=path), self.assertRaises(Rejected):
                selected_file(self.repo, path)
        with self.assertRaises(Rejected):
            library_image(self.repo, 'not-a-real-config', '0', 'full')
        with self.assertRaises(Rejected):
            library_image(self.repo, self.key, '../../', 'full')
        self.assertEqual(library_image(self.repo, self.key, '0', 'full'), (b'RIFF_current_ai_hero', 'image/webp'))

    def test_symlink_refused(self):
        self.hero_path.unlink()
        target = self.repo / 'secret.webp'
        target.write_bytes(b'secret')
        self.hero_path.symlink_to(target)
        with self.assertRaises(Rejected):
            selected_file(self.repo, self.hero_url)

    def test_local_http_library_is_read_only(self):
        root = self.repo / 'assets'
        for sub in ('ingest-drop', 'staging', 'masters', 'receipts'):
            (root / sub).mkdir(parents=True)
        server = MediaManagerServer(('127.0.0.1', 0), self.repo, root)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f'http://127.0.0.1:{server.server_port}'
        with urlopen(base + '/api/library') as response:
            self.assertEqual(response.status, 200)
            data = json.loads(response.read())
            self.assertEqual(data['count'], 26)
            self.assertIn('not live PROD', data['source'])
        key = self.key.replace(':', '%3A')
        with urlopen(base + f'/api/library-image?key={key}&photo=0&size=full') as response:
            self.assertEqual(response.headers.get_content_type(), 'image/webp')
            self.assertEqual(response.read(), b'RIFF_current_ai_hero')
        with self.assertRaises(HTTPError) as error:
            urlopen(base + '/api/library-image?key=..%2Fsecret&photo=0&size=full')
        self.assertEqual(error.exception.code, 400)

    def test_index_metadata_not_legacy_photo_registry(self):
        rows = current_library(self.repo)
        selected = next(row for row in rows if row['key'] == self.key)
        self.assertEqual(selected['photos'][0]['source'], 'G1 approved AI placeholder')
        sets = self.repo / 'frontend/src/components/catalog/photoSetIndex.json'
        doc = json.loads(sets.read_text())
        doc['sets']['ai-placeholder']['entries'][self.key][0]['media']['src'] = \
            '/products/media/refine/retired_archetype.webp'
        sets.write_text(json.dumps(doc))
        with self.assertRaisesRegex(Rejected, 'retired/legacy'):
            current_library(self.repo)


if __name__ == '__main__':
    unittest.main()

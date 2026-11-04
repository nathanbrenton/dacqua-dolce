"""F4 local GUI security and publication tests. Uses only synthetic images."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pt54f4_manager import (MAX_UPLOAD, MediaManagerServer, Rejected, batch_dir,
                              current_state, safe_name, save_upload)


class FilenameTests(unittest.TestCase):
    def test_family_specific_names(self):
        common = {'role': 'system', 'sequence': '1', 'version': '3', 'extension': 'png'}
        self.assertEqual(safe_name(dict(common, family='refine', size='1-5', material='neoprene',
                                        valve='clack5', style='archetype')),
                         'refine_1-5_neoprene_clack5_archetype_system_01_v03.png')
        self.assertEqual(safe_name(dict(common, family='harmony', size='2-0', material='stainless')),
                         'harmony_2-0_stainless_system_01_v03.png')
        self.assertEqual(safe_name(dict(common, family='origin', variant='standard')),
                         'origin_standard_system_01_v03.png')

    def test_invalid_or_inapplicable_metadata(self):
        ok = {'family': 'refine', 'size': '1-5', 'material': 'stainless', 'valve': 'clack3',
              'style': 'realistic', 'role': 'system', 'sequence': '1', 'version': '1', 'extension': 'png'}
        for change in ({'family': '../evil'}, {'valve': 'clack'}, {'extension': 'svg'},
                       {'sequence': '0'}, {'version': '100'}, {'sequence': '1.0'},
                       {'role': 'membrane'}, {'role': 'brine', 'family': 'essence'}):
            with self.subTest(change=change), self.assertRaises(Rejected):
                safe_name(dict(ok, **change))


@unittest.skipUnless(shutil.which('magick'), 'ImageMagick required for synthetic tests')
class LocalServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        self.repo, self.root = home / 'repo', home / 'assets'
        (self.repo / 'frontend/src/components/catalog').mkdir(parents=True)
        (self.repo / 'frontend/public/products/media').mkdir(parents=True)
        (self.repo / 'frontend/src/components/catalog/publishedPhotoIndex.json').write_text(
            '{"schema_version":1,"entries":[]}\n', encoding='utf-8')
        for part in ('ingest-drop', 'staging', 'masters', 'receipts'):
            (self.root / part).mkdir(parents=True)
        self.server = MediaManagerServer(('127.0.0.1', 0), self.repo, self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.meta = {'family': 'refine', 'size': '1-5', 'material': 'neoprene',
                     'valve': 'clack5', 'style': 'archetype', 'role': 'system',
                     'sequence': '1', 'version': '1', 'extension': 'png'}
        self.photo = home / 'source.png'
        subprocess.run(['magick', '-size', '64x96', 'xc:white', str(self.photo)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def request(self, route, body=None, headers=None, method=None):
        req = Request(self.base + route, data=body, headers=headers or {}, method=method)
        try:
            with urlopen(req, timeout=20) as resp:
                return resp.status, json.loads(resp.read())
        except HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def headers(self, csrf=None, kind='application/json'):
        return {'Origin': self.base, 'X-PT54-CSRF': csrf or self.server.csrf,
                'Content-Type': kind}

    def post(self, route, payload, csrf=None):
        return self.request(route, json.dumps(payload).encode(), self.headers(csrf), 'POST')

    def test_no_automatic_publication_and_explicit_workflow(self):
        code, state = self.request('/api/state')
        self.assertEqual(code, 200)
        self.assertEqual(state['published_count'], 0)
        self.assertEqual(state['csrf'], self.server.csrf)
        query = __import__('urllib.parse', fromlist=['urlencode']).urlencode(self.meta)
        code, uploaded = self.request('/api/upload?' + query, self.photo.read_bytes(),
                                      self.headers(kind='application/octet-stream'), 'POST')
        self.assertEqual(code, 200, uploaded)
        self.assertEqual(uploaded['upload']['status'], 'intake_only')
        self.assertEqual(current_state(self.repo, self.root)['published_count'], 0)
        code, result = self.post('/api/prepare', {'filename': uploaded['upload']['name']})
        self.assertEqual(code, 200, result)
        name = result['batch']['name']
        self.assertEqual(result['batch']['count'], 1)
        self.assertEqual(current_state(self.repo, self.root)['published_count'], 0)
        with urlopen(self.base + f'/preview/{name}/0', timeout=10) as response:
            self.assertEqual(response.headers.get_content_type(), 'image/webp')
            self.assertTrue(response.read().startswith(b'RIFF'))
        code, denied = self.post('/api/publish', {'batch': name, 'approval': 'wrong', 'confirmed': True})
        self.assertEqual(code, 400, denied)
        self.assertEqual(current_state(self.repo, self.root)['published_count'], 0)
        code, planned = self.post('/api/plan', {'batch': name})
        self.assertEqual(code, 200, planned)
        self.assertEqual(len(planned['items']), 1)
        code, accepted = self.post('/api/publish', {'batch': name, 'approval': name, 'confirmed': True})
        self.assertEqual(code, 200, accepted)
        self.assertEqual(current_state(self.repo, self.root)['published_count'], 1)
        self.assertTrue(Path(accepted['receipt']).is_file())
        code, again = self.post('/api/publish', {'batch': name, 'approval': name, 'confirmed': True})
        self.assertEqual(code, 400, again)

    def test_upload_never_overwrites_and_invalid_image_is_removed(self):
        name = safe_name(self.meta)
        ok = save_upload(self.repo, self.root, self.meta, self.photo.read_bytes())
        self.assertEqual(ok['name'], name)
        with self.assertRaisesRegex(Rejected, 'already exists'):
            save_upload(self.repo, self.root, self.meta, self.photo.read_bytes())
        self.meta['version'] = '2'
        with self.assertRaises(Rejected):
            save_upload(self.repo, self.root, self.meta, b'not a real png')
        self.assertFalse((self.root / 'ingest-drop' / safe_name(self.meta)).exists())
        with self.assertRaises(Rejected):
            save_upload(self.repo, self.root, self.meta, b'X' * (MAX_UPLOAD + 1))

    def test_csrf_and_host_are_enforced(self):
        code, _ = self.post('/api/prepare', {'filename': None}, csrf='invalid')
        self.assertEqual(code, 403)
        code, _ = self.request('/api/prepare', b'{}', {'Content-Type': 'application/json'}, 'POST')
        self.assertEqual(code, 403)
        req = Request(self.base + '/api/state', headers={'Host': 'attacker.invalid'})
        with self.assertRaises(HTTPError) as cm:
            urlopen(req, timeout=10)
        self.assertEqual(cm.exception.code, 403)

    def test_invalid_batch_id(self):
        for name in ('../../etc', 'batch-../demo', 'example', 'batch-é'):
            with self.assertRaises(Rejected):
                batch_dir(self.root, name)


if __name__ == '__main__':
    unittest.main()

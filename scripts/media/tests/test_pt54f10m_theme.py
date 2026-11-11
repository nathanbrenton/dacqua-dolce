"""PT54-F10M: theme options read canonical TEST source; no publishing or writes."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from pt54f10m_theme import theme_options, theme_stylesheet, theme_logo
from pt54f4_manager import MediaManagerServer

class ThemeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        theme = self.repo / 'frontend/src/theme'
        theme.mkdir(parents=True)
        source = Path(__file__).resolve().parents[3] / 'frontend/src/theme'
        for name in ('themes.ts','appearance.ts','typography.ts','branding.ts','tokens.css'):
            (theme / name).write_bytes((source/name).read_bytes())
        self.assertTrue((self.repo / 'frontend/public/brand/logos').mkdir(parents=True, exist_ok=True) is None)
        # One known legitimate logo in an isolated fixture; never use public internet.
        (self.repo/'frontend/public/brand/logos/dacqua-dolce-logo-metallic-aqua-transparent.webp').write_bytes(b'RIFFfixtureWEBP')
        (self.repo/'frontend/src/components/catalog').mkdir(parents=True)
        (self.repo/'frontend/src/components/catalog/publishedPhotoIndex.json').write_text('{}')
        self.asset = Path(self.tmp.name)/'photo-library'
        for d in ('ingest-drop','staging','masters','receipts'):
            (self.asset/d).mkdir(parents=True)

    def test_canonical_choices_and_defaults(self):
        result = theme_options(self.repo)
        self.assertEqual(len(result['themes']), 6)
        self.assertEqual(len(result['typography']), 6)
        self.assertEqual(len(result['logos']), 4)
        self.assertEqual([a['id'] for a in result['appearance']], ['light','dark'])
        self.assertEqual(result['defaults']['theme'], 'lagoon-editorial')
        self.assertEqual(result['defaults']['appearance'], 'light')
        self.assertEqual(result['defaults']['logo'], 'metallic-aqua')
        self.assertIn('surface', theme_stylesheet(self.repo).decode('utf-8'))

    def test_logo_allowlist_and_symlink(self):
        self.assertEqual(theme_logo(self.repo,'metallic-aqua'),b'RIFFfixtureWEBP')
        with self.assertRaises(ValueError): theme_logo(self.repo,'../../secrets')
        (self.repo/'frontend/src/theme/tokens.css').unlink()
        (self.repo/'frontend/src/theme/tokens.css').symlink_to(Path('/etc/hosts'))
        with self.assertRaises(ValueError): theme_stylesheet(self.repo)

    def test_http_readonly_theme_routes(self):
        server = MediaManagerServer(('127.0.0.1',0),self.repo,self.asset)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            for path, kind in [('/api/theme-options','application/json'),('/site-theme-tokens.css','text/css'),
                               ('/media-theme.css','text/css'),('/media-theme.js','text/javascript'),
                               ('/site-logo?id=metallic-aqua','image/webp')]:
                con = HTTPConnection('127.0.0.1',server.server_port,timeout=5)
                con.request('GET',path)
                response = con.getresponse()
                self.assertEqual(response.status,200,path)
                self.assertIn(kind,response.getheader('Content-Type'))
                self.assertTrue(response.read())
                con.close()
            con = HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            con.request('GET','/site-logo?id=../../secrets')
            self.assertEqual(con.getresponse().status,400)
            con.close()
        finally:
            server.shutdown();server.server_close();thread.join(timeout=5)

    def test_theme_does_not_change_publishing_routes(self):
        code = (HERE/'pt54f4_manager.py').read_text()
        self.assertIn("if url.path == '/api/publish'", code)
        self.assertNotIn("if url.path == '/api/theme-options':\n                    with self.server.change_lock",code)

if __name__ == '__main__': unittest.main()

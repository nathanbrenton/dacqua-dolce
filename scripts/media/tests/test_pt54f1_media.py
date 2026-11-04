"""PT54-F1 scanner regression tests. No external dependencies, no source modifications."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / 'pt54f1_media.py'
spec = importlib.util.spec_from_file_location('pt54f1_media', FILE)
assert spec is not None and spec.loader is not None
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class NamingTests(unittest.TestCase):
    def test_refine(self):
        result = media.parse_asset_name('refine_1-5_neoprene_clack5_archetype_system_01_v03.png')
        self.assertEqual(result['family'], 'refine')
        self.assertEqual(result['valve'], 'clack5')
        self.assertEqual(result['version'], 3)

    def test_essence(self):
        result = media.parse_asset_name('essence_2-0_stainless_performance_realistic_angle_02_v01.tif')
        self.assertEqual(result['role'], 'angle')

    def test_harmony_without_valve(self):
        result = media.parse_asset_name('harmony_1-5_neoprene_pureline_01_v01.png')
        self.assertNotIn('valve', result)

    def test_origin_without_fake_tank_attributes(self):
        result = media.parse_asset_name('origin_remineralization_system_01_v02.png')
        self.assertEqual(result['variant'], 'remineralization')
        self.assertNotIn('size', result)

    def test_reject_incomplete_and_legacy_clack(self):
        for name in ('refine_1-5_neoprene_clack_archetype_system_01_v01.png',
                     'refine_1-5_neoprene_clack5_archetype_system_00_v01.png',
                     'refine_1-5_neoprene_clack5_archetype_system_01_v00.png',
                     'REFINE_1-5_neoprene_clack5_archetype_system_01_v01.png',
                     '../refine_1-5_neoprene_clack5_archetype_system_01_v01.png',
                     'origin_remineralization_system_01_v01.exe'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                media.parse_asset_name(name)


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.manifests = self.repo / 'frontend/public/products/media/refine/manifests'
        self.manifests.mkdir(parents=True)
        self.registry = self.repo / 'frontend/src/components/catalog/productMediaRegistry.ts'
        self.registry.parent.mkdir(parents=True)
        self.registry.write_text('// fixture\n')
        self.external = self.root / 'assets'
        self.inbox = self.external / 'ingest-drop'
        self.inbox.mkdir(parents=True)

    def test_legacy_manifest_reads_and_reports_missing(self):
        good_path = 'frontend/public/products/media/refine/real.webp'
        img = self.repo / good_path
        img.write_bytes(b'test')
        (self.manifests / 'asset.json').write_text(json.dumps({
            'configuration': 'refine_1-5_stainless_clack_archetype',
            'assets': {'website_webp': {'path': good_path},
                       'missing_thumb': {'path': 'frontend/public/products/media/refine/missing.webp'},
                       'unsafe': {'path': '../../bad-file'}}}))
        old = media.read_legacy_manifests(self.repo)
        self.assertEqual(old['count'], 1)
        self.assertEqual(old['asset_paths_checked'], 2)
        self.assertEqual(len(old['missing_paths']), 1)
        self.assertEqual(len(old['unsafe_paths']), 1)
        self.assertTrue(img.exists())

    def test_scanner_rejects_bad_name_and_does_not_rewrite(self):
        bad = self.inbox / 'untitled.png'
        bad.write_bytes(b'not actually an image')
        result = media.scan_inbox(self.inbox)
        self.assertEqual(result['file_count'], 1)
        self.assertEqual(len(result['rejected']), 1)
        self.assertEqual(bad.read_bytes(), b'not actually an image')

    def test_scanner_rejects_symlink(self):
        target = self.root / 'outside.png'
        target.write_bytes(b'xxx')
        (self.inbox / 'linked.png').symlink_to(target)
        result = media.scan_inbox(self.inbox)
        self.assertEqual(result['unsafe_items'], ['linked.png'])

    def test_no_write_mode_leaves_repo_intact(self):
        result = media.build_report(self.repo, self.external)
        self.assertEqual(result['mode'], 'inspection_only')
        self.assertEqual(result['legacy']['count'], 0)
        self.assertEqual(sorted(x.name for x in self.inbox.iterdir()), [])

    def test_safe_relative_path(self):
        self.assertTrue(media.safe_relative_path('frontend/public/products/media/refine/x.webp'))
        for path in ('../../etc/passwd', '/etc/passwd', 'C:\\etc\\passwd', '', None):
            self.assertFalse(media.safe_relative_path(path))


if __name__ == '__main__':
    unittest.main()

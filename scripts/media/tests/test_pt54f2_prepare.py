"""PT54-F2 non-destructive preparation regression tests."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pt54f2_prepare import (Rejected, collect_candidates, prepare, targets_for, verify)  # noqa: E402


@unittest.skipUnless(shutil.which('magick'), 'ImageMagick is required for these tests')
class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'assets'
        self.repo = Path(self.temp.name) / 'repo'
        for path in [self.root / 'ingest-drop', self.root / 'staging',
                     self.repo / 'frontend/public/products/media']:
            path.mkdir(parents=True)

    def source(self, name='refine_1-5_stainless_clack5_archetype_system_01_v01.png'):
        path = self.root / 'ingest-drop' / name
        subprocess.run(['magick', '-size', '112x140', 'xc:white', '-fill', '#1c78c8',
                        '-draw', 'rectangle 15,20 55,90', str(path)], check=True,
                       capture_output=True)
        return path

    def test_prepare_six_artifacts_and_source_unchanged(self):
        original = self.source()
        content = original.read_bytes()
        batch = prepare(self.root, self.repo)
        verify(batch)
        self.assertEqual(original.read_bytes(), content)
        self.assertEqual(len(list(batch.glob('items/*/manifest.json'))), 1)
        self.assertEqual(len(list(batch.glob('items/*/website/*'))), 2)
        self.assertEqual(len(list(batch.glob('items/*/thumbnails/*'))), 2)
        self.assertEqual(len(list(batch.glob('items/*/master/*'))), 1)
        item = json.loads(next(batch.glob('items/*/manifest.json')).read_text())
        self.assertEqual(item['status'], 'review_pending')
        self.assertEqual(len(item['files']), 5)
        self.assertEqual(len(list(self.repo.rglob('*.*'))), 0)
        self.assertTrue((batch / 'review.html').is_file())
        self.assertTrue((batch / 'batch.json').is_file())
        broken = batch / item['files']['website_png']['path']
        broken.write_bytes(b'tampered')
        with self.assertRaisesRegex(Rejected, 'differs from recorded checksum'):
            verify(batch)

    def test_empty_intake_never_builds_batch(self):
        with self.assertRaisesRegex(Rejected, 'empty'):
            collect_candidates(self.root)
        self.assertFalse(list((self.root / 'staging').iterdir()))

    def test_reject_duplicate_photo_slot(self):
        self.source('refine_1-5_stainless_clack5_archetype_system_01_v01.png')
        self.source('refine_1-5_stainless_clack5_archetype_system_01_v02.png')
        with self.assertRaises(Rejected):
            collect_candidates(self.root)
        self.assertFalse(list((self.root / 'staging').iterdir()))

    def test_single_filename_allows_controlled_revision_selection(self):
        one = 'refine_1-5_stainless_clack5_archetype_system_01_v01.png'
        self.source(one)
        self.source('refine_1-5_stainless_clack5_archetype_system_01_v02.png')
        self.assertEqual(len(collect_candidates(self.root, one)), 1)
        with self.assertRaises(Rejected):
            collect_candidates(self.root, '../evil.png')

    def test_symlink_intake_entry_rejected(self):
        src = self.source()
        (self.root / 'ingest-drop' / 'refine_1-5_stainless_clack5_realistic_system_01_v01.png').symlink_to(src)
        with self.assertRaises(Rejected):
            collect_candidates(self.root)

    def test_family_dependent_proposed_paths(self):
        item = {'name': 'origin_standard_system_01_v02.webp',
                'identity': {'family': 'origin', 'variant': 'standard'}}
        paths = targets_for(item)
        self.assertEqual(paths['master'], 'masters/origin/origin_standard_system_01_v02.webp')
        self.assertIn('generated/manifests/origin_standard_system_01_v02.json', paths['manifest'])


if __name__ == '__main__':
    unittest.main()

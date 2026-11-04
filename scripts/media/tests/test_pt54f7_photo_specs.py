"""PT54-F7: photo requirements match the current backend, not invented upload rules."""
from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGE = ROOT / "scripts/media/pt54f4_ui.html"
F1 = ROOT / "scripts/media/pt54f1_media.py"
F2 = ROOT / "scripts/media/pt54f2_prepare.py"
F4 = ROOT / "scripts/media/pt54f4_manager.py"


class PhotoRequirementsTests(unittest.TestCase):
    def test_reference_exists_and_is_before_upload(self):
        html = PAGE.read_text('utf-8')
        self.assertEqual(html.count('id="photo-specs-title"'), 1)
        self.assertEqual(html.count('id="photo-specs-details"'), 1)
        self.assertLess(html.index('id="photo-specs-title"'), html.index('id="drop"'))

    def test_visible_specification_matches_implemented_limits(self):
        html = PAGE.read_text('utf-8')
        self.assertIn('64 MiB', html)
        self.assertIn('256 MiB', html)
        self.assertIn('50 megapixels', html)
        self.assertIn('16 px wide', html)
        self.assertIn('1122 × 1402 px', html)
        self.assertIn('384 × 480 px', html)
        self.assertIn('lossless WebP', html)
        self.assertIn('does not crop or upscale', html)
        self.assertIn('MAX_UPLOAD = 64 * 1024 * 1024', F4.read_text('utf-8'))
        self.assertIn('MAX_SOURCE_BYTES = 256 * 1024 * 1024', F1.read_text('utf-8'))
        self.assertIn('MAX_PIXELS = 50_000_000', F2.read_text('utf-8'))
        self.assertIn("WEB_MAX = '1122x1402>'", F2.read_text('utf-8'))
        self.assertIn("THUMB_MAX = '384x480>'", F2.read_text('utf-8'))

    def test_file_formats_and_filename_examples(self):
        html = PAGE.read_text('utf-8')
        for name in ('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff'):
            self.assertIn(name, html)
        for name in ('refine_1-5_neoprene_clack5_archetype_system_01_v03.png',
                     'harmony_1-5_stainless_tank_02_v01.png',
                     'origin_remineralization_system_01_v02.png'):
            self.assertIn(name, html)
        for word in ('Refine/Essence', 'Harmony example', 'Origin example'):
            self.assertIn(word, html)
        self.assertIn('FAMILIES =', F1.read_text('utf-8'))


if __name__ == '__main__':
    unittest.main()

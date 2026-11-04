"""PT54-F3: simulate publications with generated synthetic images, never real media."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pt54f2_prepare import prepare
from pt54f3_publish import Rejected, load_index, plan, publish


@unittest.skipUnless(shutil.which('magick'), 'ImageMagick required for synthetic photo tests')
class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / 'repo'
        self.root = base / 'assets'
        (self.repo / 'frontend/public/products/media').mkdir(parents=True)
        (self.repo / 'frontend/src/components/catalog').mkdir(parents=True)
        (self.repo / 'frontend/src/components/catalog/publishedPhotoIndex.json').write_text(
            '{"schema_version":1,"entries":[]}\n', encoding='utf-8')
        for folder in ('ingest-drop', 'staging', 'masters', 'receipts'):
            (self.root / folder).mkdir(parents=True)

    def image(self, filename: str):
        destination = self.root / 'ingest-drop' / filename
        subprocess.run(['magick', '-size', '64x96', 'xc:white', str(destination)], check=True)
        return destination

    def stage(self, filename: str):
        self.image(filename)
        return prepare(self.root, self.repo, filename)

    def test_explicit_approval_and_revisions(self):
        file_one = 'refine_1-5_neoprene_clack5_archetype_system_01_v01.png'
        batch = self.stage(file_one)
        items, index = plan(self.root, self.repo, batch)
        self.assertEqual(len(items), 1)
        self.assertEqual(index['entries'], [])
        self.assertEqual(load_index(self.repo)['entries'], [])
        with self.assertRaises(Rejected):
            publish(self.root, self.repo, batch, 'wrong-batch')
        receipt = publish(self.root, self.repo, batch, batch.name)
        self.assertTrue(receipt.is_file())
        entries = load_index(self.repo, check_assets=True)['entries']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['configuration'], 'refine:1.5:neoprene:clack:archetype')
        self.assertEqual(entries[0]['photographed_valve'], 'clack5')
        self.assertTrue(entries[0]['src'].startswith('/products/media/refine/generated/'))
        with self.assertRaises(Rejected):
            publish(self.root, self.repo, batch, batch.name)

        file_two = 'refine_1-5_neoprene_clack5_archetype_system_01_v02.png'
        other_batch = self.stage(file_two)
        publish(self.root, self.repo, other_batch, other_batch.name)
        entries = load_index(self.repo, check_assets=True)['entries']
        self.assertEqual([e['version'] for e in entries], [1, 2])
        self.assertTrue((self.root / 'masters/refine' / file_one).is_file())
        self.assertTrue((self.root / 'masters/refine' / file_two).is_file())

    def test_no_mixed_clack_models(self):
        one = self.stage('essence_2-0_stainless_clack5_realistic_detail_01_v01.png')
        publish(self.root, self.repo, one, one.name)
        two = self.stage('essence_2-0_stainless_clack3_realistic_angle_02_v01.png')
        with self.assertRaisesRegex(Rejected, 'Clack3/Clack5'):
            plan(self.root, self.repo, two)

    def test_origin_and_variable_slots(self):
        batch = self.stage('origin_standard_angle_02_v01.png')
        publish(self.root, self.repo, batch, batch.name)
        entries = load_index(self.repo, check_assets=True)['entries']
        self.assertEqual(entries[0]['configuration'], 'origin:DD5RO')
        self.assertEqual(entries[0]['sequence'], 2)

    def test_reject_symlinked_destination(self):
        name = 'harmony_1-5_stainless_detail_02_v01.png'
        batch = self.stage(name)
        target = self.repo / 'frontend/public/products/media/harmony/generated'
        target.parent.mkdir(parents=True)
        target.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(Rejected):
            plan(self.root, self.repo, batch)

    def test_tampered_asset_rejected(self):
        name = 'origin_remineralization_membrane_01_v01.png'
        batch = self.stage(name)
        image = next((batch / 'items').rglob('*.webp'))
        image.write_bytes(b'tampered')
        with self.assertRaises(Rejected):
            plan(self.root, self.repo, batch)
        self.assertEqual(load_index(self.repo)['entries'], [])

    def test_source_stays_intact(self):
        name = 'refine_1-5_stainless_performance_realistic_valve_02_v01.png'
        source = self.image(name)
        original = source.read_bytes()
        batch = prepare(self.root, self.repo, name)
        publish(self.root, self.repo, batch, batch.name)
        self.assertEqual(source.read_bytes(), original)
        self.assertTrue(load_index(self.repo, check_assets=True))


if __name__ == '__main__':
    unittest.main()

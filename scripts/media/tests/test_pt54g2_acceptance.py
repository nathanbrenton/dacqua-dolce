"""G2 source-side integrity and acceptance guardrails without photo IO."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'pt54g2_acceptance.py'
spec = importlib.util.spec_from_file_location('pt54g2_acceptance',SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class G2AcceptanceTests(unittest.TestCase):
    def test_record_never_marks_production_approved(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.object(mod,'OUT',Path(t)):
                with patch.object(mod,'datetime',wraps=mod.datetime):
                    report={'production_approved':False,'maintenance_notice_technical_and_legal_review':'pending before production publication'}
                    mod.record(report)
                    files=list(Path(t).glob('pt54g2-test-visual-acceptance-*.json'))
                    self.assertEqual(len(files),1)
                    data=json.loads(files[0].read_text())
                    self.assertEqual(data['production_approved'],False)
                    self.assertIn('pending',data['maintenance_notice_technical_and_legal_review'])

    def test_legacy_inventory_never_deletes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for family in mod.FAMILIES:
                folder=root/family
                folder.mkdir()
                (folder/'historical.webp').write_bytes(b'a sample')
            with patch.object(mod,'MEDIA',root):
                counts=mod.inventory_legacy()
            self.assertEqual({k:v['retained_files'] for k,v in counts.items()},
                             {k:1 for k in mod.FAMILIES})
            for family in mod.FAMILIES:
                self.assertTrue((root/family/'historical.webp').exists())


if __name__=='__main__': unittest.main()

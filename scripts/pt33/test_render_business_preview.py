import copy
import json
import tempfile
import unittest
from pathlib import Path
import render_business_preview as render
import plan_business as core

ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'docs/production/pt33'

class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((DOCS/'business-manifest.example.json').read_text())
        cls.inventory=json.loads((DOCS/'offline-inventory.example.json').read_text())
    def p(self): return core.plan(self.m,'b'*40)
    def test_inventory_valid(self):
        self.assertEqual(render.validate_inventory(self.inventory),self.inventory['reserved'])
    def test_missing_inventory_section_rejected(self):
        x=copy.deepcopy(self.inventory);del x['reserved']['ports']
        with self.assertRaises(ValueError):render.validate_inventory(x)
    def test_collision_port(self):
        x=copy.deepcopy(self.inventory);x['reserved']['ports'].append(8100)
        self.assertTrue(render.collision_checks(self.p(),render.validate_inventory(x)))
    def test_nested_path_collision(self):
        x=copy.deepcopy(self.inventory);x['reserved']['paths'].append('/srv/sample-business/data')
        self.assertTrue(render.collision_checks(self.p(),render.validate_inventory(x)))
    def test_no_collision_sample(self):
        self.assertEqual(render.collision_checks(self.p(),render.validate_inventory(self.inventory)),[])
    def test_previews_no_secret_value(self):
        files=render.render(self.m,self.p())
        self.assertEqual(len(files),6)
        self.assertTrue(all(name.endswith(('.txt','.json')) for name in files))
        self.assertIn('ownership_verified": false', files['06-provider-ownership.preview.json'])
    def test_deterministic_render(self):
        self.assertEqual(render.render(self.m,self.p()),render.render(self.m,self.p()))
    def test_main_output_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'rendered'
            argv=['--manifest',str(DOCS/'business-manifest.example.json'),'--schema',str(DOCS/'business-manifest.schema.json'), '--inventory',str(DOCS/'offline-inventory.example.json'),'--source-revision','b'*40,'--output-dir',str(out)]
            self.assertEqual(render.main(argv),0)
            self.assertFalse(json.loads((out/'00-plan.json').read_text())['ready_to_apply'])
            self.assertEqual(render.main(argv),2)
    def test_refuses_arbitrary_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            real=base/'real';real.mkdir()
            alias=base/'alias';alias.symlink_to(real, target_is_directory=True)
            out=alias/'preview'
            argv=['--manifest',str(DOCS/'business-manifest.example.json'),
                  '--schema',str(DOCS/'business-manifest.schema.json'),
                  '--inventory',str(DOCS/'offline-inventory.example.json'),
                  '--source-revision','b'*40,'--output-dir',str(out)]
            self.assertEqual(render.main(argv),2)
            self.assertFalse((real/'preview').exists())

    def test_refuses_collision_before_creation(self):
        with tempfile.TemporaryDirectory() as td:
            x=copy.deepcopy(self.inventory);x['reserved']['ports'].append(8100)
            inv=Path(td)/'inventory.json';inv.write_text(json.dumps(x))
            out=Path(td)/'out'
            argv=['--manifest',str(DOCS/'business-manifest.example.json'),'--schema',str(DOCS/'business-manifest.schema.json'), '--inventory',str(inv),'--source-revision','b'*40,'--output-dir',str(out)]
            self.assertEqual(render.main(argv),2)
            self.assertFalse(out.exists())

if __name__=='__main__': unittest.main()

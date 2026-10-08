import copy
import importlib.util
import json
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name('plan_business.py')
SPECPATH = Path(__file__).resolve().parents[2] / 'docs/production/pt33'
spec = importlib.util.spec_from_file_location('pt33_planner', MODULE)
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)

class PlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((SPECPATH / 'business-manifest.schema.json').read_text())
        cls.example = json.loads((SPECPATH / 'business-manifest.example.json').read_text())

    def issues(self, value):
        x = planner.validate_schema(value, self.schema)
        return x or planner.semantic_checks(value)

    def test_example_valid(self):
        self.assertEqual(self.issues(self.example), [])

    def test_protected_identity(self):
        x = copy.deepcopy(self.example)
        x['database']['name'] = 'dacqua_dolce'
        self.assertTrue(self.issues(x))

    def test_shared_role(self):
        x = copy.deepcopy(self.example)
        x['database']['runtime_role'] = x['database']['migrator_role']
        self.assertTrue(self.issues(x))

    def test_historical_restore_rejected(self):
        x = copy.deepcopy(self.example)
        x['data']['mode'] = 'restore'
        self.assertTrue(self.issues(x))

    def test_unapproved_seed_rejected(self):
        x = copy.deepcopy(self.example)
        x['data']['seed_profile'] = 'dacqua'
        self.assertTrue(self.issues(x))

    def test_domain_duplicate(self):
        x = copy.deepcopy(self.example)
        x['network']['aliases'] = [x['network']['canonical_host']]
        self.assertTrue(self.issues(x))

    def test_path_traversal(self):
        x = copy.deepcopy(self.example)
        x['instance']['service_root'] = '/srv/foo/../bar'
        self.assertTrue(self.issues(x))

    def test_unknown_field(self):
        x = copy.deepcopy(self.example)
        x['business']['secret_value'] = 'abc'
        self.assertTrue(self.issues(x))

    def test_plan_not_apply_ready(self):
        p = planner.plan(self.example, 'a' * 40)
        self.assertFalse(p['ready_to_apply'])
        self.assertTrue(all(not i['ownership_verified'] for i in p['provider_accounts_required']))

if __name__ == '__main__':
    unittest.main()

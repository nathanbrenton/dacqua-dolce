"""Offline integration acceptance cases for PT33-B v0.5."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

from evidence_contract import SECTIONS, EXTRA_SECTIONS, NGINX_SECTIONS, PROVIDERS, section_digest
from verify_business_resources import main, verify, safe_report_output

ROOT = Path(__file__).resolve().parents[2]


class IntegratedVerificationTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT / 'docs/production/pt33/business-manifest.schema.json').read_text())
        self.manifest = json.loads((ROOT / 'docs/production/pt33/business-manifest.example.json').read_text())
        self.now = dt.datetime(2026, 10, 9, 5, 0, tzinfo=dt.timezone.utc)
        self.evidence = {
            'evidence_version': 2, 'resource_scope': 'single_debian_host_read_only',
            'host_id': 'sample-host', 'target_instance_id': self.manifest['instance']['id'],
            'source': 'read_only_host_collector', 'collector_version': 'test-fixture',
            'collected_at_utc': self.now.isoformat(),
            'sections': {key: self.entry() for key in SECTIONS + EXTRA_SECTIONS + NGINX_SECTIONS},
            'external_verification': {key: 'unverified' for key in PROVIDERS},
            'ready_to_apply': False,
        }

    @staticmethod
    def entry(values=(), status='partial'):
        values = list(values)
        return {'status': status, 'values': values, 'method': 'fixture',
                'detail': 'offline simulation', 'sha256': section_digest(values)}

    def test_integrated_partial_is_non_authorizing(self):
        result = verify(self.manifest, self.evidence, self.schema, now=self.now)
        self.assertFalse(result['ready_to_apply'])
        self.assertTrue(result['host_assessment']['unverified'])
        self.assertEqual(set(result['independent_provider_ownership']), set(PROVIDERS))

    def test_positive_collisions_remain_visible_in_partial(self):
        self.evidence['sections']['database_roles'] = self.entry(['sample_runtime'])
        self.evidence['sections']['nginx_server_names'] = self.entry(['*.example.test'])
        result = verify(self.manifest, self.evidence, self.schema, now=self.now)
        self.assertIn('database_roles', {c['category'] for c in result['host_assessment']['collisions']})
        self.assertIn('nginx_server_names', {c['category'] for c in result['host_assessment']['collisions']})
        self.assertFalse(result['ready_to_apply'])

    def test_stale_refused(self):
        with self.assertRaisesRegex(ValueError, 'stale'):
            verify(self.manifest, self.evidence, self.schema, now=self.now + dt.timedelta(hours=25))

    def test_contradictory_digest_refused(self):
        self.evidence['sections']['ports']['values'] = [8100]
        with self.assertRaisesRegex(ValueError, 'integrity'):
            verify(self.manifest, self.evidence, self.schema, now=self.now)

    def test_wrong_target_refused(self):
        self.evidence['target_instance_id'] = 'not-this-instance'
        with self.assertRaisesRegex(ValueError, 'target instance'):
            verify(self.manifest, self.evidence, self.schema, now=self.now)

    def test_invalid_manifest_refused(self):
        self.manifest['instance']['service_root'] = '/../unsafe'
        with self.assertRaisesRegex(ValueError, 'manifest'):
            verify(self.manifest, self.evidence, self.schema, now=self.now)

    def test_old_evidence_refused_for_integrated_path(self):
        self.evidence['evidence_version'] = 1
        with self.assertRaisesRegex(ValueError, 'version 2'):
            verify(self.manifest, self.evidence, self.schema, now=self.now)

    def test_report_output_rejects_arbitrary_symlink_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / 'actual').mkdir()
            (folder / 'alias').symlink_to(folder / 'actual', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'unsafe report output path'):
                safe_report_output(folder / 'alias' / 'report.json')

    def test_report_output_rejects_existing_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / 'other').write_text('untouched')
            (folder / 'report.json').symlink_to(folder / 'other')
            with self.assertRaisesRegex(ValueError, 'unsafe report output path'):
                safe_report_output(folder / 'report.json')

    def test_output_refuses_overwrite(self):
        # Run CLI with actual current timestamp so no clock manipulation is required.
        evidence = copy.deepcopy(self.evidence)
        evidence['collected_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            manifest_path, evidence_path, report_path = (folder / x for x in ('manifest.json', 'evidence.json', 'report.json'))
            manifest_path.write_text(json.dumps(self.manifest))
            evidence_path.write_text(json.dumps(evidence))
            argv = ['--manifest', str(manifest_path), '--evidence', str(evidence_path), '--output', str(report_path)]
            self.assertEqual(main(argv), 0)
            self.assertEqual(main(argv), 2)
            self.assertFalse(json.loads(report_path.read_text())['ready_to_apply'])


if __name__ == '__main__':
    unittest.main()

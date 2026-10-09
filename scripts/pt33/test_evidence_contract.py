"""v0.5 contract tests: deliberately offline and standard library only."""
import copy
import datetime as dt
import unittest
from evidence_contract import PROVIDERS, SECTIONS, section_digest, validate_v2
from evaluate_production_evidence import assess

NOW = dt.datetime(2026, 10, 9, 1, 0, tzinfo=dt.timezone.utc)
MANIFEST = {'instance': {'id':'fresh-store', 'service_user':'fresh_app',
    'systemd_unit':'fresh-api.service', 'service_root':'/srv/fresh',
    'config_root':'/etc/fresh', 'state_root':'/var/lib/fresh'},
    'network':{'port':8123}, 'database': {'name':'freshdb',
    'runtime_role':'fresh_runtime', 'migrator_role':'fresh_migrator'}}

def sample():
    return {'evidence_version':2, 'resource_scope':'single_debian_host_read_only',
      'host_id':'sanitized-host', 'target_instance_id':'fresh-store',
      'source':'reviewed_manual_inventory', 'collector_version':'pt33-v0.5',
      'collected_at_utc':'2026-10-09T00:30:00Z', 'ready_to_apply':False,
      'sections':{s:{'status':'partial', 'values':[], 'method':'reviewed_read_only',
                    'detail':'inspection cannot prove completeness', 'sha256':section_digest([])}
                  for s in SECTIONS},
      'external_verification':{provider:'unverified' for provider in PROVIDERS}}

class ContractTests(unittest.TestCase):
    def test_partial_never_clears(self):
        report=assess(MANIFEST,sample(),now=NOW)
        self.assertFalse(report['ready_to_apply'])
        self.assertEqual(len(report['not_observed']),0)
        self.assertEqual(len(report['unverified']),9)
    def test_complete_bounded_non_observation(self):
        e=sample()
        e['sections']['database_names']['status']='complete'
        report=assess(MANIFEST,e,now=NOW)
        self.assertEqual(report['not_observed'][0]['value'],'freshdb')
        self.assertFalse(report['ready_to_apply'])
    def test_positive_collision_in_partial(self):
        e=sample(); entry=e['sections']['ports']
        entry['values']=[8123]; entry['sha256']=section_digest(entry['values'])
        self.assertIn({'category':'ports','value':8123},assess(MANIFEST,e,now=NOW)['collisions'])
    def test_digest_detects_edit(self):
        e=sample(); e['sections']['ports']['values']=[8123]
        with self.assertRaisesRegex(ValueError,'integrity'):validate_v2(e,now=NOW)
    def test_expired(self):
        with self.assertRaisesRegex(ValueError,'stale'):validate_v2(sample(),now=NOW+dt.timedelta(days=2))
    def test_target_mismatch(self):
        e=sample();e['target_instance_id']='wrong'
        with self.assertRaisesRegex(ValueError,'target instance'):assess(MANIFEST,e,now=NOW)
    def test_provider_cannot_be_cleared(self):
        e=sample();e['external_verification']['postmark']='verified'
        with self.assertRaisesRegex(ValueError,'provider'):validate_v2(e,now=NOW)
    def test_failures_cannot_contain_inventory(self):
        e=sample(); item=e['sections']['ports'];item['status']='failed';item['values']=[1];item['sha256']=section_digest([1])
        with self.assertRaisesRegex(ValueError,'cannot claim'):validate_v2(e,now=NOW)
    def test_future_stamp(self):
        with self.assertRaisesRegex(ValueError,'future'):validate_v2(sample(),now=NOW-dt.timedelta(hours=1))
    def test_apply_claim_rejected(self):
        e=sample();e['ready_to_apply']=True
        with self.assertRaisesRegex(ValueError,'authorize'):validate_v2(e,now=NOW)
    def test_duplicate_values_rejected(self):
        e=sample(); item=e['sections']['ports'];item['values']=[80,80];item['sha256']=section_digest(item['values'])
        with self.assertRaisesRegex(ValueError,'duplicate'):validate_v2(e,now=NOW)
    def test_complete_scope_still_no_external_clearance(self):
        e=sample()
        for item in e['sections'].values():item['status']='complete'
        report=assess(MANIFEST,e,now=NOW)
        self.assertEqual(report['external_providers'],'UNVERIFIED')
        self.assertFalse(report['ready_to_apply'])
if __name__=='__main__': unittest.main()


class ExpandedContractTests(unittest.TestCase):
    def test_original_six_section_snapshot_valid(self):
        validate_v2(sample(), now=NOW)
    def test_extended_section_snapshot_valid(self):
        from evidence_contract import EXTRA_SECTIONS
        e=sample()
        for name in EXTRA_SECTIONS:
            e['sections'][name]={'status':'partial','values':[], 'method':'fixtures', 'detail':'bounded', 'sha256':section_digest([])}
        validate_v2(e,now=NOW)
        self.assertFalse(assess(MANIFEST,e,now=NOW)['ready_to_apply'])
    def test_binding_port_contradiction(self):
        from evidence_contract import EXTRA_SECTIONS
        e=sample()
        for name in EXTRA_SECTIONS:
            e['sections'][name]={'status':'partial','values':[], 'method':'fixtures', 'detail':'bounded', 'sha256':section_digest([])}
        binding=e['sections']['tcp_bindings']
        binding['values']=['127.0.0.1:7777']; binding['sha256']=section_digest(binding['values'])
        with self.assertRaisesRegex(ValueError, 'contradictory'):
            validate_v2(e,now=NOW)
    def test_unknown_extra_section_rejected(self):
        e=sample()
        e['sections']['unrecognized']={'status':'partial','values':[], 'method':'fixtures','detail':'', 'sha256':section_digest([])}
        with self.assertRaisesRegex(ValueError,'sections'):
            validate_v2(e,now=NOW)

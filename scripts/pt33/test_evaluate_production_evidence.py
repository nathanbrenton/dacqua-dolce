"""Offline evidence and fail-closed acceptance checks."""
import datetime as dt
import unittest
import copy
from evaluate_production_evidence import assess

NOW=dt.datetime(2026,10,8,23,30,tzinfo=dt.timezone.utc)
MANIFEST={'instance':{'service_user':'sample_app','systemd_unit':'sample-api.service','service_root':'/srv/sample','config_root':'/etc/sample','state_root':'/var/lib/sample'},'network':{'port':8100},'database':{'name':'sample','runtime_role':'sample_app','migrator_role':'sample_migrator'}}
EVIDENCE={'evidence_version':1,'host_id':'prod','source':'manual_terminal_inspection_reviewed','inspection_date_utc':'2026-10-08','collected_at_utc':None,'resource_scope':'debian_production_manual_read_only','reserved':{'service_users':['existing'],'systemd_units':['existing.service'],'paths':['/srv/dacqua-dolce'],'ports':[8000],'database_names':['dacqua_dolce'],'database_roles':['dacqua_dolce_app']},'coverage':{'service_users':'partial','systemd_units':'partial','paths':'partial','ports':'partial','database_names':'observed','database_roles':'partial'}}
class EvidenceTests(unittest.TestCase):
    def test_no_apply_authorization(self):
        result=assess(MANIFEST,EVIDENCE,NOW)
        self.assertFalse(result['ready_to_apply']);self.assertTrue(result['unverified'])
    def test_collision_is_reported(self):
        e=copy.deepcopy(EVIDENCE);e['reserved']['ports'].append(8100)
        self.assertIn({'category':'ports','value':8100},assess(MANIFEST,e,NOW)['collisions'])
    def test_parent_path_collision(self):
        e=copy.deepcopy(EVIDENCE);e['reserved']['paths'].append('/srv')
        self.assertTrue(any(x['category']=='paths' for x in assess(MANIFEST,e,NOW)['collisions']))
    def test_missing_coverage_rejected(self):
        e=copy.deepcopy(EVIDENCE);del e['coverage']['ports']
        with self.assertRaises(ValueError):assess(MANIFEST,e,NOW)
    def test_stale_rejected(self):
        with self.assertRaises(ValueError):assess(MANIFEST,EVIDENCE,NOW+dt.timedelta(days=3))
    def test_future_rejected(self):
        with self.assertRaises(ValueError):assess(MANIFEST,EVIDENCE,NOW-dt.timedelta(days=2))
    def test_wrong_source_rejected(self):
        e=copy.deepcopy(EVIDENCE);e['source']='provider_verified'
        with self.assertRaises(ValueError):assess(MANIFEST,e,NOW)
    def test_no_clock_time_proof(self):
        self.assertEqual(assess(MANIFEST,EVIDENCE,NOW)['timestamp_precision'],'calendar_day_only')
    def test_exact_timestamp_expired(self):
        e=copy.deepcopy(EVIDENCE);e['collected_at_utc']='2026-10-08T00:00:00Z'
        with self.assertRaises(ValueError):assess(MANIFEST,e,NOW+dt.timedelta(days=1))
if __name__=='__main__':unittest.main()

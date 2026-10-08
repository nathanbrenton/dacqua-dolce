import unittest
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import collect_host_inventory as c

M = {'business': {'id':'sample-business'}, 'instance':{'id':'sample-business-staging','service_user':'unlikely_pt33_user_abc','systemd_unit':'unlikely-pt33.service','service_root':'/srv/pt33-unused-abc','config_root':'/etc/pt33-unused-abc','state_root':'/var/lib/pt33-unused-abc'}, 'network':{'port':8100}}
class FakeProcess:
    def __init__(self, stdout, returncode=0): self.stdout=stdout; self.returncode=returncode
class HostInventoryTests(unittest.TestCase):
    def test_port_collision(self):
        with patch.object(c.pwd, 'getpwnam', side_effect=KeyError):
            _, seen=c.local_observations(M, system='Darwin', runner=lambda *a,**k:FakeProcess('p200\nn127.0.0.1:8100\n'))
        self.assertEqual(seen['port'],'listening')
    def test_no_port_does_not_claim_availability(self):
        with patch.object(c.pwd, 'getpwnam', side_effect=KeyError):
            with patch.object(c.socket,'gethostname',return_value='test-host'):
                report=c.build(M,system='Darwin',runner=lambda *a,**k:FakeProcess('n127.0.0.1:8888\n'))
        self.assertFalse(report['ready_to_apply'])
        self.assertFalse(report['observations']['port']['availability_verified'])
        self.assertEqual(report['observations']['port']['observation'],'not_observed_in_visible_tcp_listeners')
    def test_lsof_unavailable_remains_unverified(self):
        with patch.object(c.pwd, 'getpwnam', side_effect=KeyError):
            _, found=c.local_observations(M,'Darwin',lambda *a,**k: (_ for _ in ()).throw(FileNotFoundError()))
        self.assertEqual(found['port'],'unverified_lsof_unavailable')
    def test_scope_does_not_claim_db_or_providers(self):
        with patch.object(c.pwd, 'getpwnam', side_effect=KeyError):
            report=c.build(M,'Darwin',lambda *a,**k:FakeProcess(''))
        self.assertIn('postgresql_database_and_roles',report['unverified'])
        self.assertIn('provider_account_ownership',report['unverified'])
    def test_no_secret_fields(self):
        with patch.object(c.pwd, 'getpwnam', side_effect=KeyError):
            report=c.build(M,'Darwin',lambda *a,**k:FakeProcess(''))
        self.assertNotIn('secret',str(report).lower())
if __name__ == '__main__': unittest.main()

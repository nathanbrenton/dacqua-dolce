import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from collect_debian_evidence import inspect_nginx_names, build_v2
from evidence_contract import validate_v2
from evaluate_production_evidence import assess_v2

class Result:
    def __init__(self, stdout='', returncode=0):
        self.stdout, self.returncode = stdout, returncode

def stub(argv, **kwargs):
    if argv[:2] == ['getent', 'passwd']: return Result('demo:x:1000:1000::/home/demo:/bin/sh\n')
    if argv[:2] == ['getent', 'group']: return Result('demo:x:1000:\n')
    if argv[0] == 'systemctl': return Result('demo.service enabled enabled\n')
    if argv[0] == 'ss': return Result('LISTEN 0 10 127.0.0.1:8100 0.0.0.0:*\n')
    raise AssertionError(argv)

MANIFEST = {'instance': {'id':'sample-staging', 'service_user':'sample_user',
    'systemd_unit':'sample.service','service_root':'/srv/sample','config_root':'/etc/sample',
    'state_root':'/var/lib/sample'}, 'network': {'canonical_host':'shop.example.test',
    'aliases':['www.shop.example.test'], 'port':8123},
    'database':{'name':'sample', 'runtime_role':'sample_app','migrator_role':'sample_migrator'}}

class NginxEvidenceTests(unittest.TestCase):
    def test_disabled_is_unsupported(self):
        snap=build_v2(MANIFEST, runner=stub, system='Linux', hostname='test', now=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc))
        self.assertEqual(snap['sections']['nginx_server_names']['status'],'unsupported')
    def test_sanitized_identifiers_only(self):
        cfg='# configuration file /etc/nginx/nginx.conf:\nserver_name WWW.Shop.Example.Test *.example.test;\nproxy_set_header Authorization "Bearer topsecret";\nserver_name shop.example.test;\n'
        got=inspect_nginx_names(lambda argv, **kw: Result(cfg))
        self.assertEqual(got['values'], ['*.example.test','shop.example.test','www.shop.example.test'])
        self.assertEqual(got['status'],'partial')
        self.assertNotIn('topsecret',str(got))
    def test_failed_query_not_clear(self):
        got=inspect_nginx_names(lambda argv, **kw: Result(returncode=1))
        self.assertEqual(got['status'],'failed')
        self.assertEqual(got['values'],[])
    def test_ambiguous_name_not_accepted(self):
        got=inspect_nginx_names(lambda argv, **kw: Result('server_name ~^secret-(?<name>.*)$;\n'))
        self.assertEqual(got['values'],[])
        self.assertIn('ambiguous',got['detail'])
    def test_collision_and_non_clearance(self):
        stamp=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc)
        snap=build_v2(MANIFEST, runner=stub, system='Linux', hostname='test', now=stamp,
            nginx_runner=lambda argv, **kw: Result('server_name *.example.test;\n'))
        validate_v2(snap,now=stamp)
        report=assess_v2(MANIFEST,snap,now=stamp)
        self.assertTrue(any(v['category']=='nginx_server_names' for v in report['collisions']))
        self.assertFalse(report['ready_to_apply'])
        self.assertEqual(report['nginx_effective_configuration'],'UNVERIFIED')
    def test_no_name_does_not_clear(self):
        stamp=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc)
        snap=build_v2(MANIFEST, runner=stub, system='Linux', hostname='test', now=stamp,
            nginx_runner=lambda argv, **kw: Result('server_name unrelated.example;\n'))
        report=assess_v2(MANIFEST,snap,now=stamp)
        self.assertTrue(any(v['category']=='nginx_server_names' for v in report['unverified']))

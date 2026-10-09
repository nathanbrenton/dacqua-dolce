import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import collect_debian_evidence as c
from evidence_contract import validate_v2

MANIFEST = {'instance': {'id': 'sample-staging'}}
class Process:
    def __init__(self, stdout='', returncode=0):
        self.stdout, self.returncode = stdout, returncode

def runner(argv, **kwargs):
    if argv[0] == 'getent':
        return Process('alice:x:1000:1000::/home/alice:/bin/sh\n')
    if argv[0] == 'systemctl':
        return Process('demo.service enabled enabled\nexample.timer disabled disabled\n')
    if argv[0] == 'ss':
        return Process('LISTEN 0 128 127.0.0.1:8100 0.0.0.0:*\n')
    raise AssertionError('Unexpected external executable: ' + repr(argv))

class DebianEvidenceTests(unittest.TestCase):
    def test_valid_but_never_complete(self):
        snap = c.build_v2(MANIFEST, system='Linux', hostname='demo', runner=runner,
                          now=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc))
        validate_v2(snap, now=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc))
        self.assertFalse(snap['ready_to_apply'])
        self.assertEqual(snap['sections']['ports']['values'], [8100])
        self.assertEqual(snap['sections']['systemd_units']['status'], 'partial')
        self.assertEqual(snap['sections']['database_names']['status'], 'unsupported')
        self.assertTrue(all(x == 'unverified' for x in snap['external_verification'].values()))
    def test_failed_command_does_not_clear(self):
        sections = c.collect_sections(lambda argv, **kw: Process(returncode=1))
        self.assertEqual(sections['service_users']['status'], 'failed')
        self.assertEqual(sections['ports']['values'], [])
        self.assertNotEqual(sections['ports']['status'], 'complete')
    def test_malformed_output_does_not_clear(self):
        def malformed(argv, **kwargs):
            return Process('corrupt\n')
        sections = c.collect_sections(malformed)
        self.assertEqual(sections['service_users']['status'], 'partial')
        self.assertEqual(sections['ports']['status'], 'partial')
    def test_nonlinux_rejected(self):
        with self.assertRaises(ValueError):
            c.build_v2(MANIFEST, system='Darwin')
    def test_no_shell_and_no_secret_queries(self):
        called = []
        def record(argv, **kwargs):
            called.append((argv, kwargs))
            return Process('')
        c.collect_sections(record)
        self.assertEqual([x[0][0] for x in called], ['getent', 'getent', 'systemctl', 'systemctl', 'ss'])
        self.assertTrue(all(isinstance(x[0], list) and x[1].get('check') is False for x in called))

if __name__ == '__main__': unittest.main()

class ExpandedEvidenceTests(unittest.TestCase):
    def test_numeric_id_and_group_observations(self):
        def fixture(argv, **kwargs):
            if argv[:2] == ['getent','passwd']:
                return Process('alice:x:1000:1000::/home/alice:/bin/sh\nbob:x:1000:1000::/home/bob:/bin/sh\n')
            if argv[:2] == ['getent','group']:
                return Process('staff:x:1000:alice,bob\nops:x:1000:\n')
            if argv[0] == 'systemctl': return Process('ops.service enabled enabled\n')
            if argv[0] == 'ss': return Process('LISTEN 0 128 [::]:443 [::]:*\nLISTEN 0 10 127.0.0.1:8100 0.0.0.0:*\n')
            raise AssertionError(argv)
        snap = c.build_v2(MANIFEST, runner=fixture, system='Linux', hostname='demo', now=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc))
        self.assertEqual(snap['sections']['unix_uids']['values'], [1000])
        self.assertEqual(snap['sections']['unix_gids']['values'], [1000])
        self.assertEqual(snap['sections']['unix_groups']['values'], ['ops','staff'])
        self.assertEqual(snap['sections']['tcp_bindings']['values'], ['127.0.0.1:8100','[::]:443'])
        self.assertEqual(snap['sections']['ports']['values'], [443,8100])
        self.assertTrue(all(snap['sections'][name]['status'] != 'complete' for name in ('unix_uids','unix_gids','unix_groups','tcp_bindings')))
    def test_group_command_failure_distinct_from_empty(self):
        def fixture(argv, **kwargs):
            if argv[:2] == ['getent','group']: return Process(returncode=2)
            return Process('')
        result=c.collect_sections(fixture)
        self.assertEqual(result['unix_groups']['status'], 'failed')
        self.assertEqual(result['unix_gids']['status'], 'failed')
    def test_malformed_group_is_partial(self):
        def fixture(argv, **kwargs):
            if argv[:2] == ['getent','group']: return Process('ops:x:1001:\nbadgroup\n')
            return Process('')
        result=c.collect_sections(fixture)
        self.assertEqual(result['unix_groups']['values'], ['ops'])
        self.assertEqual(result['unix_groups']['status'], 'partial')
    def test_invalid_socket_does_not_get_clearance(self):
        def fixture(argv, **kwargs):
            if argv[0] == 'ss': return Process('LISTEN 0 10 not-an-address:8000 *:*\n')
            return Process('')
        result=c.collect_sections(fixture)
        self.assertEqual(result['tcp_bindings']['status'], 'partial')
        self.assertEqual(result['ports']['values'], [])

class FilesystemAndSystemdTests(unittest.TestCase):
    def test_existing_candidate_is_collision_observation(self):
        from types import SimpleNamespace
        def probe(path):
            if path == '/srv/other':
                return SimpleNamespace(st_mode=0o040755)
            raise FileNotFoundError(path)
        result = c.collect_sections(runner, candidate_paths=['/srv/other'], path_probe=probe)
        self.assertEqual(result['paths']['values'], ['/srv/other'])
        self.assertEqual(result['paths']['status'], 'partial')

    def test_missing_candidate_does_not_clear(self):
        def probe(path): raise FileNotFoundError(path)
        result = c.collect_sections(runner, candidate_paths=['/srv/new'], path_probe=probe)
        self.assertEqual(result['paths']['values'], [])
        self.assertEqual(result['paths']['status'], 'partial')

    def test_ancestor_symlink_treated_as_collision(self):
        from types import SimpleNamespace
        def probe(path):
            if path == '/srv/link': return SimpleNamespace(st_mode=0o120777)
            raise FileNotFoundError(path)
        result = c.collect_sections(runner, candidate_paths=['/srv/link/new'], path_probe=probe)
        self.assertEqual(result['paths']['values'], ['/srv/link/new'])

    def test_permission_failure_never_clears(self):
        def probe(path): raise PermissionError(path)
        result = c.collect_sections(runner, candidate_paths=['/srv/private'], path_probe=probe)
        self.assertEqual(result['paths']['status'], 'partial')
        self.assertIn('denied access', result['paths']['detail'])

    def test_invalid_candidate_refused(self):
        for candidate in ('relative/path', '/srv/../etc', '/'):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                c.collect_sections(runner, candidate_paths=[candidate])

    def test_unit_sources_union_and_partial_failure(self):
        def mixed(argv, **kwargs):
            if argv[:2] == ['systemctl', 'list-unit-files']:
                return Process('installed.service enabled enabled\n')
            if argv[:2] == ['systemctl', 'list-units']:
                return Process('runtime.service loaded active running test\n')
            return runner(argv, **kwargs)
        result = c.collect_sections(mixed)
        self.assertEqual(result['systemd_units']['values'], ['installed.service', 'runtime.service'])
        self.assertEqual(result['systemd_units']['status'], 'partial')
        def one_failed(argv, **kwargs):
            if argv[:2] == ['systemctl', 'list-units']:
                return Process(returncode=1)
            return mixed(argv, **kwargs)
        result = c.collect_sections(one_failed)
        self.assertEqual(result['systemd_units']['values'], ['installed.service'])
        self.assertEqual(result['systemd_units']['status'], 'partial')

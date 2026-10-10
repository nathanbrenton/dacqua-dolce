import importlib.util
from pathlib import Path
import subprocess
import unittest

MODULE = Path(__file__).with_name('collect_admin_metadata.py')
spec = importlib.util.spec_from_file_location('collector', MODULE)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class FakeResult:
    def __init__(self, out=b'', code=0, err=b'PRIVATE ERROR'):
        self.stdout, self.stderr, self.returncode = out, err, code


class SafetyTests(unittest.TestCase):
    def test_nginx_sanitization(self):
        s = collector.nginx_names('server_name Example.COM *.test.example;\nproxy_pass http://secret:token@private;\n')
        self.assertEqual(s['values'], ['*.test.example', 'example.com'])
        self.assertNotIn('token', repr(s))

    def test_nginx_rejects_regex_and_variables(self):
        s = collector.nginx_names('server_name $hostname ~^private;')
        self.assertEqual(s['status'], 'partial')
        self.assertEqual(s['values'], [])
        self.assertIn('ambiguous', s['detail'])

    def test_postgres_rejects_duplicates(self):
        self.assertEqual(collector.postgres_names('foo\nfoo\n')['status'], 'failed')

    def test_postgres_rejects_invalid(self):
        self.assertEqual(collector.postgres_names('foo\nbar\x00\n')['status'], 'failed')

    def test_empty_success_still_partial(self):
        self.assertEqual(collector.postgres_names('')['status'], 'partial')

    def test_failure_never_claims_empty_success(self):
        report = collector.collect(lambda *a, **k: FakeResult(code=1))
        self.assertTrue(all(s['status'] == 'failed' for s in report['sections'].values()))
        self.assertFalse(report['ready_to_apply'])

    def test_exact_hardcoded_commands(self):
        seen = []
        def mock(argv, **kwargs):
            seen.append((argv, kwargs))
            return FakeResult()
        collector.collect(mock)
        self.assertEqual(len(seen), 3)
        self.assertEqual(seen[0][0], ['sudo', '-n', '/usr/sbin/nginx', '-T'])
        self.assertTrue(all(c[0][:6] == ['sudo', '-n', '-u', 'postgres', '/usr/bin/psql', '-X'] for c in seen[1:]))
        self.assertTrue(all(c[1]['capture_output'] for c in seen))
        self.assertTrue(all(c[1]['env'] == collector.ENV for c in seen))

    def test_timeout_is_failed(self):
        def mock(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], 12)
        self.assertIsNone(collector.invoke(['x'], mock))

    def test_large_output_is_failed(self):
        self.assertIsNone(collector.invoke(['x'], lambda *a, **kw: FakeResult(b'x' * (collector.LIMIT + 1))))

    def test_digest_deterministic(self):
        self.assertEqual(collector.section(['b', 'a', 'a'])['sha256'], collector.section(['a', 'b'])['sha256'])

    def test_cannot_authorize(self):
        report = collector.collect(lambda *a, **kw: FakeResult())
        self.assertIs(report['ready_to_apply'], False)
        self.assertNotIn('proxy_pass', repr(report))


if __name__ == '__main__':
    unittest.main()

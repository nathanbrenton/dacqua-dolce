import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from collect_debian_evidence import inspect_postgres_metadata, build_v2
from evaluate_production_evidence import assess_v2
from test_nginx_evidence import MANIFEST, stub, Result

class PostgresEvidenceTests(unittest.TestCase):
    def test_default_opt_out(self):
        e=build_v2(MANIFEST, runner=stub, system='Linux', hostname='test', now=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc))
        self.assertEqual(e['sections']['database_roles']['status'], 'unsupported')

    def test_catalog_names_and_collision(self):
        stamp=dt.datetime(2026,10,8,tzinfo=dt.timezone.utc)
        def fake(argv, **kw):
            self.assertEqual(argv[:6], ['psql','-X','-w','-A','-t','-d'])
            self.assertEqual(argv[6], 'postgres')
            self.assertNotIn('PGPASSWORD', kw['env'])
            return Result('sample\npostgres\n' if 'pg_database' in argv[-1] else 'sample_app\nother\n')
        e=build_v2(MANIFEST, runner=stub, system='Linux', now=stamp, hostname='test', postgres_runner=fake)
        self.assertEqual(e['sections']['database_names']['status'], 'partial')
        report=assess_v2(MANIFEST,e,now=stamp)
        self.assertTrue(any(x['category']=='database_names' for x in report['collisions']))
        self.assertTrue(any(x['category']=='database_roles' for x in report['collisions']))
        self.assertFalse(report['ready_to_apply'])

    def test_failed_query_never_clears(self):
        got=inspect_postgres_metadata(lambda argv, **kw: Result(returncode=2))
        for sec in got.values():
            self.assertEqual(sec['status'], 'failed')
            self.assertEqual(sec['values'], [])

    def test_partial_failure_retains_other_positive_observations(self):
        def fake(argv, **kw):
            return Result('sample\n') if 'pg_database' in argv[-1] else Result(returncode=1)
        got=inspect_postgres_metadata(fake)
        self.assertEqual(got['database_names']['values'], ['sample'])
        self.assertEqual(got['database_roles']['status'], 'failed')

    def test_reject_malformed_and_duplicate(self):
        for bad in ('sample\nsample\n', 'bad\x01name\n'):
            got=inspect_postgres_metadata(lambda argv, **kw: Result(bad))
            self.assertTrue(all(x['status']=='failed' for x in got.values()))

    def test_does_not_query_secret_catalogs(self):
        seen=[]
        def fake(argv, **kw):
            seen.append(' '.join(argv))
            return Result('')
        inspect_postgres_metadata(fake)
        self.assertEqual(len(seen),2)
        self.assertTrue(all('pg_authid' not in q and 'password' not in q.lower() and 'pg_shadow' not in q for q in seen))

if __name__ == '__main__': unittest.main()

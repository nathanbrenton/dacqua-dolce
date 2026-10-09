"""PT35 runner contract tests using only mocked external commands; no PostgreSQL access."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name('run_backend_regression.sh')


class PT35SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pt35-mock-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'home'
        self.root = self.base / 'repo'
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.runner = self.root / 'scripts/pt35/run_backend_regression.sh'
        self.runner.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE, self.runner)
        self.cluster = self.home / 'Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17'
        self.cluster.mkdir(parents=True)
        (self.cluster / 'PG_VERSION').write_text('17\n')
        venv = self.root / 'backend/.venv/bin'
        venv.mkdir(parents=True)
        self.log = self.base / 'actions.log'
        self._mock('uname', '#!/bin/sh\necho Darwin\n')
        self._mock('pg_ctl', '''#!/bin/sh
printf 'pg_ctl %s\\n' "$*" >> "$MOCK_LOG"
case " $* " in
  *" status "*) test "${MOCK_ALREADY_RUNNING:-0}" = 1 ;;
  *" start "*) test "${MOCK_START_FAIL:-0}" != 1 ;;
  *" stop "*) test "${MOCK_STOP_FAIL:-0}" != 1 ;;
  *) exit 2 ;;
esac
''')
        self._mock('pg_isready', '''#!/bin/sh
printf 'pg_isready %s\\n' "$*" >> "$MOCK_LOG"
test "${MOCK_PORT_OCCUPIED:-0}" = 1
''')
        self._mock('psql', '''#!/bin/sh
printf 'psql %s\\n' "$*" >> "$MOCK_LOG"
test "${MOCK_PSQL_FAIL:-0}" != 1 || exit 1
DB=''
while [ "$#" -gt 0 ]; do
  if [ "$1" = -d ]; then shift; DB="$1"; fi
  shift
done
if [ "$DB" = postgres ]; then
  if [ "${MOCK_IDENTITY_BAD:-0}" = 1 ]; then echo incorrect; else printf 'pt35_admin|postgres|55433|%s\\n' "$MOCK_CLUSTER"; fi
else
  printf 'pt35_admin|%s|55433\\n' "$DB"
fi
''')
        self._mock('createdb', '''#!/bin/sh
printf 'createdb %s\\n' "$*" >> "$MOCK_LOG"
test "${MOCK_CREATE_FAIL:-0}" != 1
''')
        self._mock('dropdb', '''#!/bin/sh
printf 'dropdb %s\\n' "$*" >> "$MOCK_LOG"
test "${MOCK_DROP_FAIL:-0}" != 1
''')
        self._mock('python', '''#!/bin/sh
printf 'python %s\\n' "$*" >> "$MOCK_LOG"
if [ "$1" = -c ]; then echo mock-temporary-encryption-key; exit 0; fi
test "${MOCK_PYTEST_FAIL:-0}" != 1
''', directory=venv)
        self._mock('alembic', '''#!/bin/sh
printf 'alembic %s\\n' "$*" >> "$MOCK_LOG"
test "${MOCK_ALEMBIC_FAIL:-0}" != 1
''', directory=venv)

    def _mock(self, name, content, directory=None):
        p = (directory or self.bin) / name
        p.write_text(content)
        p.chmod(0o755)

    def run_runner(self, **settings):
        env = os.environ.copy()
        env.update({'HOME': str(self.home), 'PATH': str(self.bin) + os.pathsep + env.get('PATH', ''),
                    'MOCK_LOG': str(self.log), 'MOCK_CLUSTER': str(self.cluster),
                    'PGHOSTADDR': '198.51.100.1',
                    'DACQUA_DATABASE_URL': 'postgresql://untrusted-host/should-not-use',
                    'DACQUA_MIGRATION_DATABASE_URL': 'postgresql://untrusted-host/should-not-use'})
        env.update({key: str(value) for key, value in settings.items()})
        result = subprocess.run(['/bin/bash', str(self.runner)], cwd=self.root, env=env,
                                capture_output=True, text=True, timeout=15)
        actions = self.log.read_text() if self.log.exists() else ''
        return result, actions

    def test_missing_cluster_refuses_without_db_commands(self):
        shutil.rmtree(self.cluster)
        res, actions = self.run_runner()
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('PT35 REFUSED', res.stderr)
        self.assertNotIn('createdb', actions)

    def test_symlinked_cluster_refuses(self):
        target = self.base / 'other'
        self.cluster.rename(target)
        self.cluster.symlink_to(target, target_is_directory=True)
        res, actions = self.run_runner()
        self.assertNotEqual(res.returncode, 0)
        self.assertNotIn('pg_ctl', actions)

    def test_wrong_pg_version_refuses(self):
        (self.cluster / 'PG_VERSION').write_text('16\n')
        res, actions = self.run_runner()
        self.assertNotEqual(res.returncode, 0)
        self.assertNotIn('createdb', actions)

    def test_competing_listener_refuses_without_start(self):
        res, actions = self.run_runner(MOCK_PORT_OCCUPIED=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('port 55433 already responds', res.stderr)
        self.assertNotIn(' start ', actions)
        self.assertNotIn('createdb', actions)

    def test_wrong_identity_stops_only_started_cluster(self):
        res, actions = self.run_runner(MOCK_IDENTITY_BAD=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('identity/data directory mismatch', res.stderr)
        self.assertIn(' stop -m fast', actions)
        self.assertNotIn('createdb', actions)

    def test_existing_cluster_wrong_identity_does_not_stop(self):
        res, actions = self.run_runner(MOCK_ALREADY_RUNNING=1, MOCK_IDENTITY_BAD=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertNotIn(' stop ', actions)
        self.assertNotIn('createdb', actions)

    def test_start_failure_never_creates_database(self):
        res, actions = self.run_runner(MOCK_START_FAIL=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertNotIn('createdb', actions)

    def test_creation_failure_does_not_drop_unverified_database(self):
        res, actions = self.run_runner(MOCK_CREATE_FAIL=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertNotIn('dropdb', actions)
        self.assertIn(' stop -m fast', actions)

    def test_migration_failure_drops_disposable_and_stops(self):
        res, actions = self.run_runner(MOCK_ALEMBIC_FAIL=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('alembic upgrade head', actions)
        self.assertRegex(actions, r'dropdb .* dacqua_pt35_run_\d{14}_\d+')
        self.assertIn(' stop -m fast', actions)
        self.assertNotIn('pytest', actions)

    def test_pytest_failure_cleans_and_preserves_error(self):
        res, actions = self.run_runner(MOCK_PYTEST_FAIL=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('pytest backend', actions)
        self.assertIn('dropdb ', actions)
        self.assertIn(' stop -m fast', actions)

    def test_success_isolates_db_and_cleans(self):
        res, actions = self.run_runner()
        self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
        self.assertRegex(actions, r'createdb .* dacqua_pt35_run_\d{14}_\d+')
        self.assertRegex(actions, r'dropdb .* dacqua_pt35_run_\d{14}_\d+')
        self.assertNotIn('dacqua_pt35_test', actions)
        self.assertIn(' stop -m fast', actions)

    def test_already_running_is_not_stopped(self):
        res, actions = self.run_runner(MOCK_ALREADY_RUNNING=1)
        self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
        self.assertNotIn(' start ', actions)
        self.assertNotIn(' stop ', actions)
        self.assertIn('dropdb ', actions)

    def test_shutdown_failure_returns_error(self):
        res, actions = self.run_runner(MOCK_STOP_FAIL=1)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('WARNING: PT35 cluster shutdown failed', res.stdout)
        self.assertIn('dropdb ', actions)

    def test_cleanup_failure_warns(self):
        res, actions = self.run_runner(MOCK_DROP_FAIL=1)
        self.assertIn('WARNING: disposable database cleanup failed', res.stdout)
        self.assertIn(' stop -m fast', actions)
        self.assertNotEqual(res.returncode, 0)


if __name__ == '__main__':
    unittest.main()

# PT35 — Isolated regression runner safety acceptance

The guarded runner is restricted to a dedicated local macOS PostgreSQL 17 cluster at `~/Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17`, on `127.0.0.1:55433`. The existing `dacqua_pt35_test` database must not be dropped. It creates a unique disposable database for each run, applies Alembic migrations, executes the backend suite, then cleans up.

## Contract tests

Run from repository root:

```bash
python3 -m unittest discover -s scripts/pt35 -p 'test_*.py' -q
```

These tests copy the runner into a temporary mocked repository with a temporary HOME. PostgreSQL commands, Python, Alembic, and the OS check are mocked, so they never connect to the real PostgreSQL cluster. Scenarios cover missing/symlinked/wrong-version cluster, occupied port, identity mismatch (running and newly started), startup failure, creation failure, migration failure, pytest failure, successful cleanup, already-running cluster preservation, and failed drop/shutdown cleanup.

The runner treats a failed disposable DB drop or failed shutdown as an unsuccessful overall run, even when pytest passed. This does not guarantee cleanup after SIGKILL, host crash, or storage failure. Manually inspect any reported cleanup failure before another run.

## Separate live acceptance

The mocked tests cannot prove live PostgreSQL isolation or shell behavior on a particular Mac. After passing mocks, run `bash scripts/pt35/run_backend_regression.sh` locally to verify real migration, regression, and normal cleanup. Confirm `pg_isready -h 127.0.0.1 -p 55433` returns no response if the runner started the cluster. Do not run live fault-injection against real databases.

No production connection, deployment, or Git operation is authorized by these checks.

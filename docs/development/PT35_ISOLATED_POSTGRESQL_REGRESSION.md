# PT35 — Isolated PostgreSQL backend regression (macOS)

## Purpose and acceptance evidence

Run the entire backend regression against a **fresh PostgreSQL database** in the dedicated, local PT35 cluster, without depending on development or production database credentials. Manual baseline: PostgreSQL 17.11; Alembic head `d921ae0c7254`; 56 public tables; **549 passed** with a disposable test-only MFA encryption key. PT33's independent guard suite: **86 passed**. These are recorded baseline results, not a promise that all future runs will pass.

The runner is a local developer utility. It does not inspect or authorize production, invoke deployment, or alter the provisioning decision `ready_to_apply=false`.

## Trusted boundary

- Dedicated data directory: `~/Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17`
- TCP: `127.0.0.1:55433` (not public or production)
- Database administrator: `pt35_admin` (created with the PT35 cluster)
- Original reusable database: `dacqua_pt35_test` — **preserved and never reset by the runner**
- Per-run database: `dacqua_pt35_run_<UTC timestamp>_<process ID>` — created fresh and dropped by the runner
- Existing Homebrew data directory `/opt/homebrew/var/postgresql@17` — outside this workflow
- Git repository and `backend/.env` — not modified by the runner

The runner checks the cluster's `PG_VERSION`, its actual PostgreSQL-reported data directory, connected user/database/port and the disposable database's identity. It refuses port occupancy by another cluster. It clears inherited libpq routing parameters and explicitly overrides runtime/migration URLs for the isolated database. Never alter these guard values to point at a real development, staging or production cluster.

**Important caveat:** The temporary cluster was initialized with PostgreSQL `trust` authentication. It is suitable only on a trusted single-user local machine with localhost-only listeners. Do not use it on shared/multi-user hosts or expose port 55433 externally. A system account with access to the machine may connect without a database password.

## One-time cluster initialization (only if the approved directory does not exist)

Run these only after confirming the target directory is absent. Do **not** repeat `initdb` on an existing cluster. Install Homebrew `postgresql@17` and the backend Python virtual environment/dependencies first.

```bash
mkdir -p "$HOME/Desktop/dacqua-dolce_build-assets/test-infrastructure"
chmod 700 "$HOME/Desktop/dacqua-dolce_build-assets/test-infrastructure"
initdb -D "$HOME/Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17" -U pt35_admin -A trust --encoding=UTF8 --no-instructions
printf "\nport = 55433\nlisten_addresses = '127.0.0.1'\nunix_socket_directories = '/tmp'\n" >> "$HOME/Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17/postgresql.conf"
```

The known PT35 cluster has already been initialized and successfully tested; this setup block is for rebuilds, not routine use.

## Routine run

From the repository root:

```bash
bash scripts/pt35/run_backend_regression.sh
```

Behavior: start PT35 PostgreSQL if stopped; refuse a competing PostgreSQL listener; verify the precise cluster; create a new run-specific DB; set test environment and randomized Fernet MFA key only for the child process; apply actual Alembic migrations; execute pytest; remove the disposable database; stop PostgreSQL **only if this runner started it**. Pytest exit status is preserved. Extra pytest arguments may be appended, e.g. `bash scripts/pt35/run_backend_regression.sh -k authentication`.

No secret connection URLs or encryption keys are printed. The test-only key is process-scoped, not written to disk. The child tests may perform outbound operations if test code is modified or configured to do so; inspect new integrations before running.

## Explicit reset / recovery

No reset of `dacqua_pt35_test` is necessary: every regression run uses a fresh disposable database. If a run is interrupted and cleanup cannot complete, inspect the remaining disposable names **on the dedicated cluster only**:

```bash
psql -h 127.0.0.1 -p 55433 -U pt35_admin -d postgres -X -Atc "SELECT datname FROM pg_database WHERE datname LIKE 'dacqua_pt35_run_%' ORDER BY datname"
```

After verifying exact identity and confirming no process still uses a named disposable database, an operator can remove **only that specific `dacqua_pt35_run_...` database** using `dropdb -h 127.0.0.1 -p 55433 -U pt35_admin -- <reviewed_database_name>`. Never bulk-drop names or delete the PGDATA directory for routine cleanup.

If testing failed, preserve the pytest output for diagnosis. If PostgreSQL shutdown failed, inspect using `pg_ctl -D "$HOME/Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17" status`; shut it down manually with the same `-D` path after checking identity. Do not operate on `/opt/homebrew/var/postgresql@17`.

## Scope of assurance

A passing run proves that this repository's backend tests pass against an isolated migrated PostgreSQL test database under the explicitly supplied test configuration. It does not establish production deployment readiness, production provider ownership, or completeness of external integrations. PT33's production evidence collection remains separately authorized and read-only.

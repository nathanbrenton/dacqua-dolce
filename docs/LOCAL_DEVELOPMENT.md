# Local Development

D'Acqua Dolce reserves a stable set of loopback ports for local development.
Keeping these ports explicit prevents bookmarks, proxy configuration, local
database URLs, and development instructions from drifting between sessions.

## Canonical local port registry

| Service | Host endpoint | Purpose |
| --- | --- | --- |
| React / Vite frontend | `127.0.0.1:15173` | Browser-facing local development UI |
| FastAPI / Uvicorn backend | `127.0.0.1:8000` | Local API and health/readiness endpoints |
| PostgreSQL Docker host mapping | `127.0.0.1:15432` | PostgreSQL access from macOS host tools and the locally run backend |
| PostgreSQL inside the Docker network | `postgres:5432` | Native PostgreSQL container port; do not change to the host port |

These are **local-development assignments only**. Production intentionally uses
its separately documented loopback ports, including PostgreSQL `5432` and
Uvicorn `8000`. Do not mechanically replace production port references with the
local-development values.

Docker Engine itself does not receive a D'Acqua Dolce application port. Port
`15432` is the host-side published port for the PostgreSQL container; the
container continues listening on PostgreSQL's native port `5432`.

## Start local PostgreSQL

From the repository root, start the Docker Compose infrastructure using the
project's normal environment configuration. The Compose mapping publishes the
container's PostgreSQL `5432` as host-only `127.0.0.1:15432`.

The backend development database URL therefore uses port `15432` when the
backend runs directly on macOS. Keep real credentials in the untracked
`backend/.env`; use `backend/.env.example` only as a template.

## Start the backend

From `backend/`:

    .venv/bin/uvicorn app.main:app \
      --reload \
      --host 127.0.0.1 \
      --port 8000

The local API is then available at:

    http://127.0.0.1:8000

## Start the frontend

From `frontend/`:

    npm run dev

Vite is configured to bind to `127.0.0.1:15173` and proxy application API,
health, and readiness requests to `127.0.0.1:8000`.

Open:

    http://127.0.0.1:15173

## Configuration rule

When adding local services, assign and document a deliberate loopback-only host
port rather than borrowing a production port. Keep container-native ports and
production loopback ports unchanged unless the corresponding architecture is
being intentionally redesigned.


## Application environment identity

Local backend development defaults to `DACQUA_ENVIRONMENT=development`.
Automated tests explicitly identify as `test`; production deployment requires
`production`. See `docs/ENVIRONMENT_IDENTITY.md`.

Frontend developer-only controls remain governed by
`VITE_DEVELOPER_MODE=true`, which is a capability flag rather than an
environment identity. `VITE_APP_ENVIRONMENT` defaults to `development` locally.


## Local PostgreSQL least-privilege model

Local development mirrors the production separation of duties while keeping a
disposable Docker DBA identity for cluster bootstrap:

- `dacqua_dolce_dba` — local Docker/bootstrap administrator; may be superuser
  inside the disposable local container; never used by FastAPI or Alembic;
- `dacqua_dolce_migrator` — owns `dacqua_dolce_dev` and application objects,
  runs Alembic, and has DDL authority without superuser/CREATEDB/CREATEROLE/
  replication/BYPASSRLS privileges;
- `dacqua_dolce_app` — FastAPI runtime role with required DML/default
  privileges, schema `USAGE`, no schema `CREATE`, and no database/table
  ownership.

`infra/.env` stores the local DBA/migrator/runtime database secrets. The
untracked `backend/.env` contains only the runtime `DACQUA_DATABASE_URL`.
Alembic uses `scripts/alembic_local.sh`, which constructs the migrator URL for
that process rather than persisting it in `backend/.env`.

Use:

    python3 scripts/configure_local_database_credentials.py

to generate distinct local DBA/migrator/runtime credentials without printing
them. To validate existing separation without rotating credentials:

    python3 scripts/configure_local_database_credentials.py --check

## Guarded local rebuild

When a clean development database is required, use:

    scripts/rebuild_local_database.sh --confirm-destroy-local-data

The explicit flag is required because this destroys the local Docker database
volume. Before destruction, the workflow takes a local `pg_dump` safety backup
under the ignored repository-local `.local-backups/` directory.

The rebuild script is development-only. Never copy its destructive reset
behavior into production.

After a rebuild:

1. run Alembic through the migrator-only wrapper:

       scripts/alembic_local.sh upgrade head

2. reconcile/seed the supported local catalog;
3. bootstrap canonical dev/test users with `scripts/bootstrap_dev_users.py`;
4. keep reusable dev account passwords in
   `~/.dacqua-dolce/dev-bootstrap.env`, outside Git.

Canonical dev/test identities use `@dacquadolce.test`; production identities
are never populated from that fixture set.


## PT53 policy portability in Local/Dev/Test

Policy data is environment-local PostgreSQL state. Application deployment does not copy policy rows between environments. Production PostgreSQL is authoritative for live approved policy versions.

For a deliberate non-production mirror of Production policy lifecycle state, set this only in the Local/Dev/Test backend runtime:

    DACQUA_POLICY_IMPORT_ALLOW_LIFECYCLE_PRESERVATION=true

Then use Operations Policy Management to load a Production `Export all` bundle, preview it, resolve conflicts, and apply the lifecycle-preserving import. Repeating the same import should be idempotent.

Do **not** enable lifecycle-preserving import in Production. Production imports should use the default safe draft-only behavior, and Production should never be treated as a passive mirror of Local/Dev/Test.

# Local Development

D'Acqua Dolce reserves a stable set of loopback ports for local development.
Keeping these ports explicit prevents bookmarks, proxy configuration, local
database URLs, and development instructions from drifting between sessions.

## Canonical local port registry

| Service | Host endpoint | Purpose |
| --- | --- | --- |
| React / Vite frontend | `127.0.0.1:15173` | Browser-facing local development UI |
| FastAPI / Uvicorn backend | `127.0.0.1:18080` | Local API and health/readiness endpoints |
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
      --port 18080

The local API is then available at:

    http://127.0.0.1:18080

## Start the frontend

From `frontend/`:

    npm run dev

Vite is configured to bind to `127.0.0.1:15173` and proxy application API,
health, and readiness requests to `127.0.0.1:18080`.

Open:

    http://127.0.0.1:15173

## Configuration rule

When adding local services, assign and document a deliberate loopback-only host
port rather than borrowing a production port. Keep container-native ports and
production loopback ports unchanged unless the corresponding architecture is
being intentionally redesigned.

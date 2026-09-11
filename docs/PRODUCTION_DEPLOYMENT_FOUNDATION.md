# D'Acqua Dolce — Production Deployment Foundation

## Scope

This milestone defines the production runtime/deployment structure without
provisioning a specific server.

It deliberately does not commit:

- production secrets;
- database passwords;
- Postmark credentials;
- TLS private keys;
- S3 credentials;
- Vultr API credentials;
- host-specific DNS values.

## Filesystem layout

Recommended production layout:

    /srv/dacqua-dolce/
      current -> /srv/dacqua-dolce/releases/<release>
      releases/
      shared/

    /etc/dacqua-dolce/
      backend.env

Application files should be owned by a dedicated `dacqua` service account.

The runtime secret file should be root-owned and readable only by the service
group as required.

## Backend

FastAPI/Uvicorn listens only on:

    127.0.0.1:8000

It is never bound directly to the public interface.

Nginx is the public reverse proxy.

## Frontend

Vite produces static production assets in:

    frontend/dist/

Nginx serves those assets directly.

The SPA fallback uses:

    try_files $uri $uri/ /index.html;

so History API routes such as `/account`, `/operations`, and product detail
routes continue to work when loaded directly.

## systemd

The API unit:

    dacqua-dolce-api.service

uses:

    /etc/dacqua-dolce/backend.env

and runs under a dedicated `dacqua` account.

The API service has several systemd sandboxing controls enabled. These should
be tested on the actual production distribution before being considered final.

A one-shot readiness check and timer are also included.

## Nginx / TLS

The Nginx example contains placeholders for:

    example.com

and Let's Encrypt certificate paths.

Do not install it unchanged.

Before enabling the HTTPS server:

1. DNS must resolve to the production server.
2. the canonical production hostname must be chosen;
3. a certificate must be issued;
4. `DACQUA_PUBLIC_ORIGIN` must match the canonical HTTPS origin.

Password-reset links must continue to use the configured canonical origin, not
request Host headers.

## Release strategy

Production uses immutable timestamped release directories.

A deployment builds a new release, runs Alembic, builds the frontend, then
atomically changes:

    /srv/dacqua-dolce/current

to the new release.

The previous release remains available for application rollback.

## Database rollback warning

Application rollback and database rollback are not the same operation.

Alembic migrations are applied before the release becomes current.

Do not automatically downgrade PostgreSQL during an application rollback.
Migrations must be designed with backward-compatible deployment sequencing or
handled explicitly.

## Dependency installation

Python dependency authority is:

    backend/pyproject.toml

with the validated transitive resolution constrained by:

    backend/constraints-known-good.txt

Production installs the backend project without the `dev` extra. This keeps
test-only tooling such as `httpx2`, pytest, Ruff, Bandit, and pip-audit out of
the production runtime while retaining runtime `httpx`, which is required by
the Postmark integration.

The deployment script installs the local backend project rather than using a
separate `requirements.txt`.

Frontend production dependencies continue to use:

    npm ci

For repeatable local recovery, downloaded/build assets remain outside Git under:

    ~/Desktop/dacqua-dolce_build-assets/

The local Python wheelhouse contains macOS/Apple-Silicon binary wheels and is
not automatically suitable for the Debian production host.

If production requires offline installation, prepare and validate a separate
wheelhouse matching the production OS, architecture, and Python version. The
deployment script accepts its server-side location through:

    DACQUA_PYTHON_WHEELHOUSE=/path/to/python-wheels

See `docs/PYTHON_DEPENDENCY_POLICY.md` for the authoritative rebuild and
HTTP-client compatibility policy.

## Next production milestones

After the runtime templates are validated, production work proceeds in this
order:

1. Vultr host provisioning and SSH hardening.
2. Native PostgreSQL creation and role/database initialization.
3. Nginx + DNS + TLS.
4. application release deployment.
5. Postmark production configuration.
6. pgBackRest + private S3 repository + WAL/PITR.
7. nftables/fail2ban/Monit.
8. Prometheus/exporters/Alertmanager/Alloy/Loki/Grafana.
9. Better Stack independent external checks and heartbeat.
10. restore test and production launch checklist.

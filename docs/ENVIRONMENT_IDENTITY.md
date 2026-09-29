# Environment Identity

D'Acqua Dolce treats application environment as an explicit safety boundary.

## Backend identity

`DACQUA_ENVIRONMENT` resolves to one canonical value:

- `development` — local development;
- `test` — automated test execution;
- `production` — commissioned production runtime.

The backend exposes `settings.is_development`, `settings.is_test`, and
`settings.is_production`. Legacy aliases (`dev`, `testing`, and `prod`) are
normalized by application configuration for compatibility, but production
deployment tooling deliberately requires the exact value `production`.

The application default remains `development` so a developer checkout does not
become production merely because configuration is absent. Production therefore
fails closed at deployment time: `deploy_release.sh` refuses to continue unless
`/etc/dacqua-dolce/backend.env` supplies exactly:

    DACQUA_ENVIRONMENT=production

Tests set `DACQUA_ENVIRONMENT=test` before application imports so test audit
events and future environment-aware behavior are distinguishable from local
development.

## Frontend identity

Frontend build identity is separate from Vite's build mode.

- `VITE_APP_ENVIRONMENT=development|test|production` identifies the deployed
  application environment.
- `VITE_DEVELOPER_MODE=true|false` is a capability flag for developer-only UI.

Developer mode is not an environment. A production frontend build fails at
runtime initialization if it was compiled with developer mode enabled. The
production deployment helper explicitly builds with:

    VITE_APP_ENVIRONMENT=production
    VITE_DEVELOPER_MODE=false

When `VITE_APP_ENVIRONMENT` is omitted in a developer checkout, frontend
identity defaults to `development`.

## Safety rule for future external side effects

Features that can create external side effects—such as maintenance email
schedulers or commissioned payment actions—should use this environment identity
as one layer of defense:

- tests must never perform real external side effects;
- local development should use local/sandbox/provider-safe behavior;
- production side effects should require both production identity and the
  feature's own explicit commissioning/configuration boundary.

Environment identity is not a substitute for feature-level authorization,
provider sandboxing, idempotency, or explicit customer consent.


## Application identity domains

Development/test and production application identities are intentionally
visually distinct:

- development/test company identities use `@dacquadolce.test`;
- production company identities use `@dacquadolce.com`.

The canonical development fixture set belongs only to development/test.
Production must never receive the dev fixture bootstrap merely because the
application schemas are compatible.

Production UAM changes preserve existing legitimate users and migrate roles in
place. Development/test may be destructively rebuilt through the guarded local
rebuild workflow.

## Database identity is separate from application identity

`DACQUA_ENVIRONMENT` identifies the application environment. It does not grant
database authority.

FastAPI uses the runtime PostgreSQL principal `dacqua_dolce_app`; Alembic uses
`dacqua_dolce_migrator`. Application roles such as customer, employee,
administrator, and developer do not map to PostgreSQL logins.

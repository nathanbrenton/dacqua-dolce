# D'Acqua Dolce Production Deployment and Rollback

## Purpose

This document defines the production application-release lifecycle. It covers exact-source staging, release creation, database migration, catalog reconciliation, activation, validation, retention, and application rollback. Database rollback is intentionally a separate operation.

Production layout:

    /srv/dacqua-dolce/
      current -> /srv/dacqua-dolce/releases/<UTC timestamp>
      releases/
      shared/

Production configuration remains external to releases:

    /etc/dacqua-dolce/backend.env
    /etc/dacqua-dolce/migration.env

The FastAPI service receives only `backend.env`. The root-only `migration.env` is consumed by the deployment helper for Alembic and deployment-time catalog reconciliation and is not part of the runtime service environment.

PT35 sales-geography commissioning uses non-secret values in `backend.env`. The approved launch geography is `US` with the 48 contiguous states plus Washington, DC. Any explicit `DACQUA_SALES_AREA_*` values in production must continue to match `docs/PT35_SALES_GEOGRAPHY_ACTIVATION.md`; the Operations readiness snapshot reports `Action required` if runtime configuration drifts from that approved set.

For commissioned PT32 browser forms, use the readiness retry and CSP verification procedure in `PT32_COMMISSIONING_AND_RECOVERY.md` after activation. A transient `502` immediately after `systemctl restart` can precede completed Uvicorn worker startup; a persistent failure requires logs and rollback evaluation.

## Release invariants

A successfully activated release must satisfy all of the following:

- release source represents a known Git revision;
- `DACQUA_ENVIRONMENT` is explicitly `production`;
- the frontend is built with production identity and developer mode disabled;
- release directory name is a UTC timestamp in `YYYYMMDDTHHMMSSZ` form;
- release tree is owned by `root:root`;
- group/other write permission is removed from the release tree;
- runtime secrets are not copied into the release;
- backend dependencies install successfully in a release-local virtual environment;
- frontend dependencies install through `npm ci` and the production build succeeds;
- a pre-migration PostgreSQL backup is created when the commissioned helper is available;
- Alembic reaches `head` before activation;
- the canonical production catalog reconciliation completes before activation;
- `/srv/dacqua-dolce/current` is switched atomically;
- `dacqua-dolce-api.service` restarts successfully;
- local `/readiness` passes;
- the repository public production verifier passes when present;
- only successful releases participate in normal retention cleanup.

The default release-retention count is five. It may be overridden for a deployment by setting `DACQUA_RELEASE_RETENTION_COUNT` to an integer of at least two.

## Source staging boundary

Activation is deliberately separate from transport. `deploy_release.sh` accepts a complete source tree already present on the production host.

Through the 2026-09-22 checkpoint, the validated operator workflow was:

1. resolve the exact 40-character Git revision locally;
2. create `git archive --format=tar.gz` for that revision;
3. record the SHA-256 digest;
4. transfer the archive with `scp`;
5. verify the server-side SHA-256 digest;
6. extract into a revision-named staging directory under the production administrator's home;
7. validate the staged deployment script/source;
8. run the deployment helper with that staging directory.

This workflow is reproducible but retransmits the complete compressed repository snapshot for every release.

### Rsync staging helper — production validated

The repository now contains:

    scripts/production/stage_release_rsync.sh
    scripts/production/verify_staged_source.py

The staging helper is designed to replace repeated whole-archive transfers while preserving an exact-revision boundary. It:

1. resolves the requested Git revision to a full 40-character commit ID;
2. exports that exact commit to a temporary local tree, so uncommitted working-tree changes are never included;
3. writes a revision marker plus a SHA-256 manifest covering the staged source tree;
4. validates the export locally;
5. rsyncs it with checksum comparison and deletion semantics to the persistent production-admin staging cache (default `~/dacqua-dolce-deploy-source/`);
6. validates the complete staged tree again on the production host;
7. prints the separate `deploy_release.sh` activation command.

The intended local command is:

    scripts/production/stage_release_rsync.sh <revision> n8@dacqua-prod

`deploy_release.sh` also recognizes the revision marker/manifest. When they are present, it revalidates the supplied staging tree before release creation and validates the copied immutable release tree before building or migrating. Legacy archive-based staging remains accepted with a warning so existing recovery procedures are not broken.

Do **not** rsync directly into `/srv/dacqua-dolce/current` or a timestamped release. Immutable release creation, ownership normalization, activation, validation, rollback, and retention remain the responsibility of `deploy_release.sh`.

Rsync exact-revision staging is now the authoritative production transport, validated end-to-end on 2026-09-29. The legacy `git archive` + SHA-256 + `scp` workflow remains an accepted recovery fallback.

## Deployment command

From a complete release-source tree on the production host:

    sudo /path/to/release-source/scripts/production/deploy_release.sh \
      /path/to/release-source

The deployment helper performs the following ordered workflow:

1. validate root execution, source structure, both production environment files, exact production environment identity, required production values, and retention policy;
2. load the runtime configuration and separate root-only migration configuration;
3. capture the currently active release for possible rollback;
4. create a new timestamped release directory;
5. use server-side `rsync` to copy sanitized source into the immutable candidate release while excluding Git metadata, `.env*`, `node_modules`, and `.venv`;
6. create the backend virtual environment and install the constrained runtime package;
7. run `npm ci` and the frontend production build;
8. if the commissioned local PostgreSQL backup helper exists, create an on-demand pre-migration backup;
9. run `alembic upgrade head` using `DACQUA_MIGRATION_DATABASE_URL`;
10. run `./.venv/bin/python -m app.cli.seed_catalog apply` to reconcile the canonical production catalog;
11. remove the migration URL from the deployment process environment;
12. normalize the release tree to root ownership and remove group/other write permission;
13. atomically switch `current` to the candidate release;
14. restart the FastAPI systemd service;
15. wait up to approximately 30 seconds for local readiness;
16. run the public production verifier when it is included in the release;
17. automatically restore the previous application release if post-switch validation fails;
18. after successful activation, prune timestamped releases beyond the configured retention count.

A candidate that fails before activation is removed automatically. A candidate that fails post-switch validation is removed after a successful automatic rollback.

## Catalog reconciliation boundary

`backend/catalog/production_catalog.json` is the rebuild-grade baseline for seed-owned catalog metadata.

Deployment reconciliation may create/update seed-owned metadata including:

- manufacturer/category metadata;
- products by stable SKU/slug;
- repository-backed product image metadata;
- verified product specifications;
- canonical product variants/options represented in the manifest.

The current catalog source also carries the shared public Category -> Family -> Variant identity used by cards/detail pages and the accepted Essence/Origin/Refine reconciliation. Required static product media ships inside the exact Git revision; do not copy catalog images manually to production.

Reconciliation deliberately does **not** reset mutable operational state such as:

- pricing history;
- inventory quantities/reservations;
- approved claims/policies;
- jurisdiction/tax evidence;
- existing lifecycle/public-retirement state;
- customer inquiry/formal-quote availability policy;
- accounts, quotes, orders, communications, or audit evidence.

An unchanged production catalog is expected to report `total_changes 0` during deployment. Catalog reconciliation is not a substitute for restoring Production PostgreSQL during disaster recovery.

## Database-recovery ordering

For an ordinary release, the deployment helper uses the existing production database and runs the normal backup -> Alembic -> catalog sequence.

For a clean-host disaster recovery of an existing business, restore the authoritative production PostgreSQL state **before** the first current-source deployment/migration. Then deploy the intended exact Git revision so Alembic advances the restored schema to `head` and catalog reconciliation refreshes seed-owned metadata without overwriting restored business state.

Do not attempt to rebuild production by replaying historical PT releases, importing a Local/Dev/Test database, or using PT53 policy bundles as a replacement for the production database. A deliberately empty database is appropriate only for a new environment or an explicitly approved state-loss recovery plan.

The repository currently validates backups/restores through the commissioned backup/restore-check tooling, but a destructive live production restore remains an operator-controlled disaster-recovery action. Do not automate destructive database replacement without a separately rehearsed restore procedure and current backup verification.

## Migration compatibility policy

Application rollback does **not** run `alembic downgrade`.

Production migrations must therefore be designed so that the immediately previous application release can continue to operate against the migrated schema long enough for emergency application rollback. Prefer staged changes:

1. additive schema change;
2. deploy application code that can use the new schema while remaining compatible with the old path where necessary;
3. complete data transition/backfill;
4. remove obsolete application dependencies;
5. perform destructive schema cleanup only in a later release after rollback compatibility is no longer required.

A destructive migration that immediately makes the previous release unusable requires an explicit deployment plan and must not rely on ordinary application rollback.

## Automatic rollback boundary

Automatic rollback occurs only after the `current` symlink has been switched and the new release fails local readiness or public release verification.

Automatic rollback:

- switches `current` back to the previously active release;
- restarts `dacqua-dolce-api.service`;
- requires the previous release to recover local readiness;
- never downgrades PostgreSQL.

If the previous release cannot recover readiness, the deployment helper reports a critical failure and requires manual operator intervention.

## Manual rollback

List available releases:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh

Rollback to a specific timestamped release:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh \
      <release-timestamp>

The rollback helper validates the target name/path, atomically switches `current`, restarts the API, and validates the target. If that target fails validation, it restores the release that was active before the rollback attempt.

Again, PostgreSQL is not downgraded.

## Post-deployment verification

After every successful deployment, verify at minimum:

    readlink -f /srv/dacqua-dolce/current
    stat -c '%U:%G %a %n' "$(readlink -f /srv/dacqua-dolce/current)"
    curl -fsS http://127.0.0.1:8000/readiness
    curl -fsS https://dacquadolce.com/health
    systemctl status dacqua-dolce-api.service --no-pager --full
    systemctl --failed --no-pager

The current release directory must report `root:root` ownership and must not be group/other writable.

Use the repository public verifier as the canonical edge smoke test:

    /srv/dacqua-dolce/current/scripts/production/verify_release.sh \
      https://dacquadolce.com

After infrastructure smoke tests, perform browser acceptance for the user-facing surfaces changed by the release. Current high-value checks include:

- catalog card/detail Category -> Family -> Variant consistency and variant-aware media;
- product-detail footer/theme controls and customer select affordance;
- Operations product lifecycle/status labels and PT54 order-review/hold controls;
- Customer Inbox Website/Email source labels, plain-text inbound handling, and communications reply flow;
- support-form normal submission plus useful field-specific validation errors.

A real Postmark inbound test is needed only when communications transport/webhook behavior changed; do not send unnecessary live acceptance mail for unrelated releases. Spam/SPF badges are expected only when the archived inbound event actually contains those provider headers.

## Release checkpoint rule

Do not maintain a "latest production SHA" as a long-lived constant in this runbook. Determine the running release from production at the time of an operation:

    readlink -f /srv/dacqua-dolce/current
    cat /srv/dacqua-dolce/current/.dacqua-release-revision

When the release marker is unavailable on a legacy release, use the deployment history/source metadata for that release rather than guessing from documentation prose.

Documentation/rebuild changes may advance Git beyond the active production application release, and a production deployment may advance beyond the last documentation audit. Exact-revision staging plus the release marker is the authoritative source for what was deployed.

The accumulated application model is intentionally collapsed into one current-source deployment. Alembic applies every required migration in order; the canonical catalog reconcile applies current seed-owned metadata/variants/images; current frontend/server code carries the PT54, catalog-identity, Customer Inbox, support-form, and validation behavior without replaying historical releases.

## Rollback decision boundary

Use ordinary application rollback when the currently active application release is faulty but the current database schema remains compatible with the chosen older release.

Do not use ordinary application rollback when recovery requires reversing a destructive database migration. That is a separate database-recovery event and must follow the backup/restore/disaster-recovery procedure.


## Environment identity guardrail

Production deployment fails closed unless `/etc/dacqua-dolce/backend.env`
contains exactly:

    DACQUA_ENVIRONMENT=production

The deployment helper also compiles the frontend with
`VITE_APP_ENVIRONMENT=production` and `VITE_DEVELOPER_MODE=false`. The host
baseline verifier checks the backend environment identity independently. See
`docs/ENVIRONMENT_IDENTITY.md` for the application-wide model.


## PT32 Turnstile build and acknowledgement recovery

The frontend site key is public but host-local: `/etc/dacqua-dolce/turnstile-site-key`
(root-owned regular file, mode `0600`, a single site-key line). The exact-revision
deploy script reads this file and passes `VITE_TURNSTILE_SITE_KEY` into the Vite
build. The private Cloudflare secret belongs only in `/etc/dacqua-dolce/backend.env`
as `DACQUA_TURNSTILE_SECRET`, along with `DACQUA_TURNSTILE_ENABLED` and
`DACQUA_TURNSTILE_EXPECTED_HOSTNAME=dacquadolce.com`. Do not put the secret
in frontend build variables or Git. A rebuild without the host-local site key
will create a frontend with no widget; a deployment with server enforcement set
true fails before creating a release if the key/secret/hostname is missing.

**Activation sequence:** provision the site key and backend secret with
`DACQUA_TURNSTILE_ENABLED=false`; stage and deploy a reviewed exact revision;
verify the production frontend renders the widget and that quote/support forms
continue to work; enable server enforcement as a separate operator-approved
configuration step and restart the API. Be aware that existing old frontend
releases may not contain the widget: rollback to such a release must coordinate
server enforcement disabling as a separately approved break-glass procedure.

The separately commissioned Postmark transactional stream is
`website-acknowledgements`, configured by
`DACQUA_QUOTE_ACK_MESSAGE_STREAM=website-acknowledgements`. Leave
`DACQUA_QUOTE_ACK_ENABLED=false` until test delivery, staff notification,
recipient/global limit evidence, and suppressions are verified; then enable
independently. Existing `outbound` critical mail is not moved.
The protected backend runtime env, host-local public site-key file, cloud
provider configuration and production database all remain necessary rebuild
inputs alongside the exact Git revision. No automatic production/local database
sync is implied.

## Product display ordering migration (deployed)

See `PRODUCT_ORDERING_AND_TOASTS.md` before deploying revision `c1e4f9b73a62`. This adds mutable merchandising state to PostgreSQL. Database backup before migration is required by the canonical procedure. Application release rollback does not reverse schema migration; explicit Alembic downgrade drops saved family ordering data and is not an ordinary rollback procedure.


## Origin configuration presentation and mobile catalog refinement (local candidate)

See [`ORIGIN_CONFIGURATION_AND_MOBILE.md`](ORIGIN_CONFIGURATION_AND_MOBILE.md) for exact SKU/public listing behavior, local validation, deployment catalog reconciliation, inquiry labels, URL/scroll behavior, and non-destructive rollback. The current change is not yet committed or production deployed.

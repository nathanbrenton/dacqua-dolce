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

## Release invariants

A successfully activated release must satisfy all of the following:

- release source represents a known Git revision;
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

    scripts/production/stage_release_rsync.sh <revision> dacqua-prod

`deploy_release.sh` also recognizes the revision marker/manifest. When they are present, it revalidates the supplied staging tree before release creation and validates the copied immutable release tree before building or migrating. Legacy archive-based staging remains accepted with a warning so existing recovery procedures are not broken.

Do **not** rsync directly into `/srv/dacqua-dolce/current` or a timestamped release. Immutable release creation, ownership normalization, activation, validation, rollback, and retention remain the responsibility of `deploy_release.sh`.

This rsync transport becomes the authoritative standard only after its first end-to-end production deployment is validated. Until then, the previously validated `git archive` + SHA-256 + `scp` workflow remains the production fallback.

## Deployment command

From a complete release-source tree on the production host:

    sudo /path/to/release-source/scripts/production/deploy_release.sh \
      /path/to/release-source

The deployment helper performs the following ordered workflow:

1. validate root execution, source structure, both production environment files, required production values, and retention policy;
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

Deployment reconciliation may create/update:

- manufacturer metadata;
- product categories;
- products by stable SKU/slug;
- product image metadata;
- verified product specifications.

It deliberately does not reset operational state such as:

- pricing history;
- inventory quantities/reservations;
- approved claims;
- jurisdiction rules;
- existing lifecycle/approval state.

An unchanged production catalog is expected to report `total_changes 0` during deployment.

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

For a release that changes customer/account UI, perform the corresponding live browser acceptance test after infrastructure smoke tests pass. Examples include email verification, account appearance, role administration, and Operations ordering.

## Last validated checkpoint

On 2026-09-22, source commit:

    75abfd78a00c0013fb7cd91eeb3e7a873159cf7e

activated successfully as:

    /srv/dacqua-dolce/releases/20260922T173923Z

The deployment created a fresh pre-migration PostgreSQL backup, reported zero catalog changes, passed local readiness/public route/security-header validation, retained the prior release for rollback, and kept five releases.

These identifiers document a checkpoint only; future operators must deploy the intended current Git revision rather than reusing this revision blindly.

## Rollback decision boundary

Use ordinary application rollback when the currently active application release is faulty but the current database schema remains compatible with the chosen older release.

Do not use ordinary application rollback when recovery requires reversing a destructive database migration. That is a separate database-recovery event and must follow the backup/restore/disaster-recovery procedure.

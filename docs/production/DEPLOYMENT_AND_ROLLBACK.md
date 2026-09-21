# D'Acqua Dolce Production Deployment and Rollback

## Purpose

This document defines the production application-release lifecycle. It covers application artifact preparation,
activation, validation, retention, and application rollback. Database rollback is intentionally a separate operation.

Production layout:

    /srv/dacqua-dolce/
      current -> /srv/dacqua-dolce/releases/<UTC timestamp>
      releases/
      shared/

Production configuration remains external to releases:

    /etc/dacqua-dolce/backend.env

## Release invariants

A successfully activated release must satisfy all of the following:

- release directory name is a UTC timestamp in `YYYYMMDDTHHMMSSZ` form;
- release tree is owned by `root:root`;
- group/other write permission is removed from the release tree;
- runtime secrets are not copied into the release;
- backend dependencies install successfully in a release-local virtual environment;
- frontend dependencies install through `npm ci` and the production build succeeds;
- Alembic reaches `head` before activation;
- `/srv/dacqua-dolce/current` is switched atomically;
- `dacqua-dolce-api.service` restarts successfully;
- local `/readiness` passes;
- the repository public production verifier passes when present;
- only successful releases participate in normal retention cleanup.

The default release-retention count is five. It may be overridden for a deployment by setting
`DACQUA_RELEASE_RETENTION_COUNT` to an integer of at least two.

## Deployment command

From a complete release-source tree on the production host:

    sudo scripts/production/deploy_release.sh /path/to/release-source

The deployment helper performs the following ordered workflow:

1. validate root execution, source structure, environment file, required production values, and retention policy;
2. capture the currently active release for possible rollback;
3. create a new timestamped release directory;
4. copy source while excluding Git metadata, `.env*`, `node_modules`, and `.venv`;
5. create the backend virtual environment and install the constrained runtime package;
6. run `npm ci` and the frontend production build;
7. if the commissioned local PostgreSQL backup helper exists, create an on-demand pre-migration backup;
8. run `alembic upgrade head`;
9. normalize the release tree to root ownership and remove group/other write permission;
10. atomically switch `current` to the candidate release;
11. restart the FastAPI systemd service;
12. wait up to approximately 30 seconds for local readiness;
13. run the public production verifier when it is included in the release;
14. automatically restore the previous application release if post-switch validation fails;
15. after successful activation, prune timestamped releases beyond the configured retention count.

A candidate that fails before activation is removed automatically. A candidate that fails post-switch validation is
removed after a successful automatic rollback.

## Migration compatibility policy

Application rollback does **not** run `alembic downgrade`.

Production migrations must therefore be designed so that the immediately previous application release can continue to
operate against the migrated schema long enough for emergency application rollback. Prefer staged changes:

1. additive schema change;
2. deploy application code that can use the new schema while remaining compatible with the old path where necessary;
3. complete data transition/backfill;
4. remove obsolete application dependencies;
5. perform destructive schema cleanup only in a later release after rollback compatibility is no longer required.

A destructive migration that immediately makes the previous release unusable requires an explicit deployment plan and
must not rely on ordinary application rollback.

## Automatic rollback boundary

Automatic rollback occurs only after the `current` symlink has been switched and the new release fails local readiness
or public release verification.

Automatic rollback:

- switches `current` back to the previously active release;
- restarts `dacqua-dolce-api.service`;
- requires the previous release to recover local readiness;
- never downgrades PostgreSQL.

If the previous release cannot recover readiness, the deployment helper reports a critical failure and requires manual
operator intervention.

## Manual rollback

List available releases:

    sudo scripts/production/rollback_release.sh

Rollback to a specific timestamped release:

    sudo scripts/production/rollback_release.sh 20260917T084102Z

The rollback helper validates the target name/path, atomically switches `current`, restarts the API, and validates the
target. If that target fails validation, it restores the release that was active before the rollback attempt.

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

    scripts/production/verify_release.sh https://dacquadolce.com

## Rollback decision boundary

Use ordinary application rollback when the currently active application release is faulty but the current database
schema remains compatible with the chosen older release.

Do not use ordinary application rollback when recovery requires reversing a destructive database migration. That is a
separate database-recovery event and must follow the backup/restore/disaster-recovery procedure.

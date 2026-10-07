# D'Acqua Dolce Production Documentation

This directory is the authoritative documentation namespace for the D'Acqua Dolce production platform.

**Production application state represented:** PT53 deployed on 2026-10-06 at source revision `0dfc6329a4a8e9584fba4b00cba66512438fd21b`, release `/srv/dacqua-dolce/releases/20261006T175805Z`, with Alembic head `f1c4a5b76e80`. PT47-PT51 production browser acceptance is complete. PT52 and PT53 deployment smoke validation passed; their final production browser-acceptance checkpoint remains pending as of this documentation audit.

Production releases are timestamped immutable artifacts created by the standard deployment workflow. The exact source revision for a running release is recorded by release metadata/deployment output; do not treat a historical commit hash in prose as a configuration constant.

## Document set

- `ARCHITECTURE_OVERVIEW.md` — high-level platform, trust boundaries, application capabilities, policy/data authority, observability, backup model, and external dependencies.
- `REBUILD_RUNBOOK.md` — ordered rebuild workflow for recreating the production host from a fresh Debian 13 Vultr instance and the application repository.
- `OPERATIONS_REFERENCE.md` — day-to-day service, health, log, backup, account, communications, policy portability, deployment, and validation reference.
- `DEPLOYMENT_AND_ROLLBACK.md` — authoritative application release, catalog reconciliation, activation, retention, migration-compatibility, validation, and rollback workflow.
- `COMMUNICATIONS_AND_POSTMARK.md` — commissioned Cloudflare split-routing + Proton human/business mail + Postmark application mail + direct Postfix/OpenDKIM observability mail, PostgreSQL communications archive, authentication records, rebuild sequence, and production validation.
- `GRAFANA_DASHBOARDS.md` — repo-managed dashboard provisioning, access, and validation.
- `PENDING_INTEGRATIONS.md` — intentionally unfinished production items that must not be mistaken for commissioned infrastructure/application capability.

## Authority rules

1. These documents describe the **validated or explicitly noted deployed production state**, not the history of how it was reached.
2. Secrets never belong in Git. Variable names and file locations may be documented; secret values may not.
3. A component is described as commissioned only after it has been installed and validated on production. Workstation SSH should use the convenience alias `dacqua-prod`; `dacqua-platform-prod-01` is the host name, not the preferred workstation SSH target.
4. Pending work is isolated in `PENDING_INTEGRATIONS.md` rather than written into the runbook as though it already exists.
5. When production changes, update these documents in the same milestone or in the next documentation-reconciliation pass.
6. Historical planning, meeting notes, failed attempts, temporary diagnostics, and superseded implementation paths do not belong in the rebuild runbook.
7. Git is authoritative for code/schema/deployment assets. Production PostgreSQL is authoritative for live operational data and approved policies. Restic/S3 is backup/DR, not routine environment synchronization.
8. Policy portability uses explicit PT53 JSON export/import with preview. Production -> Local/Dev/Test synchronization is manual; do not clone the production database merely to synchronize policies.

## Current commerce posture

The Commerce Launch Gate remains intentionally closed. `DACQUA_LAUNCH_PHASE` defaults to `prelaunch`; `soft_launch` also keeps hosted checkout closed. Public checkout still requires production automated-tax commissioning, the exact Affinity24-provisioned gateway and payment adapter commissioning, and the remaining legal/business dependencies documented in `PENDING_INTEGRATIONS.md`.

## Older production documents

The older top-level `docs/PRODUCTION_*.md` files remain compatibility pointers and implementation history. This directory supersedes them for the current production state and rebuild procedure.

## Grafana production dashboards

The repo-managed Grafana dashboard set, provisioning layout, installation procedure, access method, and validation commands are documented in `GRAFANA_DASHBOARDS.md`.

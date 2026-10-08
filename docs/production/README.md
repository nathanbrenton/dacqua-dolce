# D'Acqua Dolce Production Documentation

This directory is the authoritative documentation namespace for the D'Acqua Dolce production platform.

**Production/rebuild state represented:** current repository capabilities through the 2026-10-07 catalog, PT54 order-review, Customer Inbox security, and public support-form hardening work. The active production SHA/release path is intentionally not hard-coded here; read it from the immutable release metadata/deployment output.

Production releases are timestamped immutable artifacts created by the standard deployment workflow. Rebuilds deploy one exact Git revision; Alembic applies the complete migration chain and the deployment helper reconciles the current canonical catalog automatically. Do not replay historical PT milestones one-by-one.

## Document set

- `ARCHITECTURE_OVERVIEW.md` — high-level platform, trust boundaries, application capabilities, policy/data authority, observability, backup model, and external dependencies.
- `REBUILD_RUNBOOK.md` — ordered rebuild workflow for recreating the production host from a fresh Debian 13 Vultr instance and the application repository.
- `OPERATIONS_REFERENCE.md` — day-to-day service, health, log, backup, account, communications, policy portability, deployment, and validation reference.
- `DEPLOYMENT_AND_ROLLBACK.md` — authoritative application release, catalog reconciliation, activation, retention, migration-compatibility, validation, and rollback workflow.
- `COMMUNICATIONS_AND_POSTMARK.md` — commissioned Cloudflare split-routing + Proton human/business mail + Postmark application mail + direct Postfix/OpenDKIM observability mail, PostgreSQL communications archive, authentication records, rebuild sequence, and production validation.
- `GRAFANA_DASHBOARDS.md` — repo-managed dashboard provisioning, access, and validation.
- `PT32_COMMISSIONING_AND_RECOVERY.md` — commissioned Turnstile, Postmark acknowledgements, Operations-only staff queue, detailed validation and recovery steps.
- `PENDING_INTEGRATIONS.md` — intentionally unfinished production items that must not be mistaken for commissioned infrastructure/application capability.

## Efficient rebuild composition

A production rebuild is composed from four authoritative layers:

1. **Git** — application source, migrations, deployment assets, repository-managed catalog metadata/images, frontend UX/security behavior, and technical documentation.
2. **Production PostgreSQL** — accounts, orders, quotes, communications, approved policies, product lifecycle, pricing/inventory, launch evidence, and other mutable business state.
3. **Protected configuration/provider state** — `/etc/dacqua-dolce/*`, DNS, Cloudflare routing, Proton/Postmark credentials, TLS private material, and other secrets that are intentionally outside Git.
4. **Host/observability state** — Debian/systemd/Nginx/PostgreSQL/monitoring configuration reconstructed from repository assets and the rebuild runbook.

For disaster recovery, restore authoritative PostgreSQL state first (or explicitly choose an empty-environment rebuild), then deploy the intended exact Git revision so Alembic and catalog reconciliation bring the restored database forward. PT53 policy bundles are not a substitute for restoring Production PostgreSQL.

Recent catalog/frontend/security changes require no separate manual installer: they travel with the exact Git revision. Product images are repository assets; PT54 schema changes travel through Alembic; current catalog metadata/variants travel through `production_catalog.json`; Customer Inbox/support-form protections travel in the application/frontend build.

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

## Product ordering and shared toast milestone (production-deployed)

See `PRODUCT_ORDERING_AND_TOASTS.md` for the local-first database ordering change, migration `c1e4f9b73a62`, staff/public acceptance, toast integration, deferred styling and schema-aware rollback. The production deployment completed at revision `3651d78ad414581e08f8908b4a142af6d2996a1f`; the initial deployment checks passed. Shared toast visual consistency remains deferred.


## Origin configuration presentation and mobile catalog refinement (local candidate)

See [`ORIGIN_CONFIGURATION_AND_MOBILE.md`](ORIGIN_CONFIGURATION_AND_MOBILE.md) for exact SKU/public listing behavior, local validation, deployment catalog reconciliation, inquiry labels, URL/scroll behavior, and non-destructive rollback. The current change is not yet committed or production deployed.

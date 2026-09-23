# D'Acqua Dolce Production Documentation

This directory is the authoritative documentation namespace for the D'Acqua Dolce production platform.

**Production state represented:** PT12/M7 communications + public support routing, validated through 2026-09-22.

Production releases are timestamped immutable artifacts created by the standard deployment workflow. The exact source revision for a running release is recorded by release metadata/deployment output; do not treat a historical commit hash in prose as a configuration constant.

## Document set

- `ARCHITECTURE_OVERVIEW.md` — high-level platform, software stack, trust boundaries, data flow, account/email boundaries, observability, backup model, and external dependencies.
- `REBUILD_RUNBOOK.md` — ordered rebuild workflow for recreating the production host from a fresh Debian 13 Vultr instance and the application repository.
- `OPERATIONS_REFERENCE.md` — day-to-day service, health, log, backup, account, email, deployment, and validation reference.
- `DEPLOYMENT_AND_ROLLBACK.md` — authoritative application release, catalog reconciliation, activation, retention, migration-compatibility, validation, and rollback workflow.
- `COMMUNICATIONS_AND_POSTMARK.md` — commissioned Cloudflare public inbound routing + Postmark outbound/inbound architecture, PostgreSQL communications archive, webhook security, rebuild sequence, and production validation.
- `GRAFANA_DASHBOARDS.md` — repo-managed dashboard provisioning, access, and validation.
- `PENDING_INTEGRATIONS.md` — intentionally unfinished production items that must not be mistaken for commissioned infrastructure.

## Authority rules

1. These documents describe the **validated production state**, not the history of how it was reached.
2. Secrets never belong in Git. Variable names and file locations may be documented; secret values may not.
3. A component is described as commissioned only after it has been installed and validated on `dacqua-platform-prod-01`.
4. Pending work is isolated in `PENDING_INTEGRATIONS.md` rather than written into the runbook as though it already exists.
5. When production changes, update these documents in the same milestone as the validated infrastructure/application change.
6. Historical planning, meeting notes, failed attempts, temporary diagnostics, and superseded implementation paths do not belong in the rebuild runbook.

## Older production documents

The older top-level `docs/PRODUCTION_*.md` files were written during bootstrap and pre-production planning. They remain useful implementation history and source material, but this directory supersedes them for the current production state and rebuild procedure.

## Grafana production dashboards

The repo-managed Grafana dashboard set, provisioning layout, installation procedure, access method, and validation commands are documented in:

    GRAFANA_DASHBOARDS.md

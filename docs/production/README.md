# D'Acqua Dolce Production Documentation

This directory is the authoritative documentation namespace for the D'Acqua Dolce production platform.

**Production state represented:** PT10, 2026-09-18.

## Document set

- `ARCHITECTURE_OVERVIEW.md` — high-level platform, software stack, trust boundaries, data flow,
  observability, backup model, and external dependencies.
- `REBUILD_RUNBOOK.md` — ordered rebuild workflow for recreating the production host from a fresh
  Debian 13 Vultr instance and the application repository.
- `OPERATIONS_REFERENCE.md` — day-to-day service, health, log, backup, deployment, and validation
  reference.
- `DEPLOYMENT_AND_ROLLBACK.md` — authoritative application release, activation, retention, migration-compatibility,
  validation, and rollback workflow.
- `PENDING_INTEGRATIONS.md` — intentionally unfinished production items that must not be mistaken for
  commissioned infrastructure.

## Authority rules

1. These documents describe the **validated production state**, not the history of how it was reached.
2. Secrets never belong in Git. Variable names and file locations may be documented; secret values may not.
3. A component is described as commissioned only after it has been installed and validated on
   `dacqua-platform-prod-01`.
4. Pending work is isolated in `PENDING_INTEGRATIONS.md` rather than written into the runbook as though it
   already exists.
5. When production changes, update these documents in the same milestone as the validated infrastructure
   change.

## Older production documents

The older top-level `docs/PRODUCTION_*.md` files were written during bootstrap and pre-production planning.
They remain useful implementation history and source material, but this directory supersedes them for the
current production state and rebuild procedure.

## Grafana production dashboards

The repo-managed Grafana dashboard set, provisioning layout, installation
procedure, access method, and validation commands are documented in:

    GRAFANA_DASHBOARDS.md

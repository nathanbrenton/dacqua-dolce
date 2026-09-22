# D'Acqua Dolce — Production Host Runbook

> **Superseded first-host runbook — retained for filename/history continuity.**
>
> The original first-host procedure has been replaced by the validated production documentation namespace under `docs/production/`.

Use:

- `docs/production/REBUILD_RUNBOOK.md` for clean-host reconstruction;
- `docs/production/OPERATIONS_REFERENCE.md` for routine operation;
- `docs/production/DEPLOYMENT_AND_ROLLBACK.md` for application releases/rollback;
- `docs/production/GRAFANA_DASHBOARDS.md` for dashboard provisioning/access;
- `docs/production/PENDING_INTEGRATIONS.md` for work that is deliberately not yet commissioned.

The current production platform includes live Postmark application email, immutable application releases, database privilege separation, repo-managed catalog bootstrap, full observability, local backup/restore validation, and production account security features that did not exist when the first-host runbook was drafted.

Current validated documentation checkpoint: 2026-09-22 / PT12.

Do not use superseded bootstrap instructions as production commands.

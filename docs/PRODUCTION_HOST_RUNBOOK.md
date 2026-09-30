# D'Acqua Dolce — Production Host Runbook

> **Superseded first-host runbook — retained for filename/history continuity.**
>
> The original first-host procedure has been replaced by the validated
> production documentation namespace under `docs/production/`.

Use:

- `docs/production/REBUILD_RUNBOOK.md` for clean-host reconstruction;
- `docs/production/OPERATIONS_REFERENCE.md` for routine operation;
- `docs/production/DEPLOYMENT_AND_ROLLBACK.md` for application releases/rollback;
- `docs/production/GRAFANA_DASHBOARDS.md` for dashboard provisioning/access;
- `docs/production/PENDING_INTEGRATIONS.md` for work that is deliberately not
  yet commissioned.

The current production platform includes live Postmark application email,
Cloudflare split inbound routing, Proton human/business mail for the commissioned
`jamie@dacquadolce.com` identity, durable Customer Inbox communications, immutable application releases,
separated PostgreSQL migrator/runtime principals, repo-managed catalog
reconciliation, capability-based application authorization, out-of-band
developer provisioning, full observability, and local backup/real-restore
validation.

The server hostname remains `dacqua-platform-prod-01`. Workstation SSH
configuration may use the convenience alias `dacqua-prod`; the alias is not a
server hostname or application configuration value.

Current application checkpoint: PT18. Email/DNS/vendor-routing documentation is validated through 2026-09-30.

Do not use superseded bootstrap instructions as production commands.

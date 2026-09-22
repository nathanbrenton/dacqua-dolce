# D'Acqua Dolce — Production Deployment Foundation

> **Superseded bootstrap document — retained for filename/history continuity.**
>
> The pre-production design that originally lived here is no longer an authoritative deployment guide. The production platform has been commissioned and materially evolved since this file was created.

Use the current production documentation instead:

- `docs/production/README.md`
- `docs/production/ARCHITECTURE_OVERVIEW.md`
- `docs/production/DEPLOYMENT_AND_ROLLBACK.md`
- `docs/production/REBUILD_RUNBOOK.md`
- `docs/production/OPERATIONS_REFERENCE.md`
- `docs/production/PENDING_INTEGRATIONS.md`

Current validated production checkpoint represented by the documentation set: 2026-09-22 / PT12.

Key changes since the original foundation planning include:

- live Vultr/Debian production host;
- native PostgreSQL 17 with separated migrator/runtime roles;
- immutable timestamped releases with automatic application rollback;
- deployment-time canonical catalog reconciliation;
- hardened FastAPI systemd service;
- full local observability stack and repo-managed Grafana dashboards;
- local PostgreSQL backup + real restore validation;
- live Postmark application transactional email;
- production customer registration/email verification/MFA/account administration;
- AWS S3/restic off-host disaster recovery still pending.

Do not copy commands or architectural assumptions from an older version of this document into production. Use `docs/production/` as the source of truth.

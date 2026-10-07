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

The active production release changes over time and is intentionally not hard-coded in this compatibility pointer. Use the immutable release metadata/deployment output for the running SHA and `docs/production/` for the authoritative rebuild target.

Key changes since the original foundation planning include:

- live Vultr/Debian production host;
- native PostgreSQL 17 with separated migrator/runtime roles;
- immutable timestamped releases with automatic application rollback;
- deployment-time canonical catalog reconciliation;
- hardened FastAPI systemd service;
- full local observability stack and repo-managed Grafana dashboards;
- local PostgreSQL backup + real restore validation;
- Cloudflare split inbound routing, Proton human/business mail, live Postmark application/customer email, PostgreSQL Customer Inbox archive, and commissioned direct Postfix/OpenDKIM observability mail;
- production customer registration/email verification/MFA/account administration;
- PT54 order-review/hold governance plus the current catalog/shared-identity and Customer Inbox/support-form hardening;
- AWS S3/restic off-host disaster recovery still pending.

Do not copy commands or architectural assumptions from an older version of this document into production. Use `docs/production/` as the source of truth.

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

Current deployed application checkpoint: PT53 on 2026-10-06 at revision `0dfc6329a4a8e9584fba4b00cba66512438fd21b`. PT47-PT51 production browser acceptance is complete; PT52/PT53 deployment smoke validation passed and final browser acceptance is pending. Use `docs/production/` for authoritative current state.

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
- AWS S3/restic off-host disaster recovery still pending.

Do not copy commands or architectural assumptions from an older version of this document into production. Use `docs/production/` as the source of truth.

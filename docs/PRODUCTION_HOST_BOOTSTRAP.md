# D'Acqua Dolce — Production Host Bootstrap

> **Superseded bootstrap document — retained for filename/history continuity.**
>
> Production host provisioning has already been completed and validated. This top-level bootstrap document is intentionally no longer a second set of rebuild instructions.

Authoritative current rebuild procedure:

    docs/production/REBUILD_RUNBOOK.md

Authoritative current architecture:

    docs/production/ARCHITECTURE_OVERVIEW.md

Authoritative current operator reference:

    docs/production/OPERATIONS_REFERENCE.md

Current production host:

    dacqua-platform-prod-01

Current validated application checkpoint: 2026-09-29 / PT18. Email/DNS/vendor-routing documentation is reconciled through 2026-09-30.

Important present-day boundaries include:

- Debian 13 / Vultr;
- public TCP 22/80/443 only;
- Nginx public edge;
- FastAPI/PostgreSQL/observability listeners private/loopback-only;
- PostgreSQL `dacqua_dolce_migrator` vs `dacqua_dolce_app` privilege separation;
- Cloudflare split routing + Proton human/business mail + Postmark application/customer mail;
- local PostgreSQL backup/restore commissioned;
- AWS S3/restic off-host repository not yet commissioned.

Do not rebuild from obsolete planning assumptions. Follow `docs/production/REBUILD_RUNBOOK.md` and the repository production assets it references.

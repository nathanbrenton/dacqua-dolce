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

Current deployed application checkpoint: PT53 on 2026-10-06 at revision `0dfc6329a4a8e9584fba4b00cba66512438fd21b`. PT47-PT51 production browser acceptance is complete; PT52/PT53 deployment smoke validation passed and final browser acceptance is pending. Use `docs/production/` for authoritative current state.

Important present-day boundaries include:

- Debian 13 / Vultr;
- public TCP 22/80/443 only;
- Nginx public edge;
- FastAPI/PostgreSQL/observability listeners private/loopback-only;
- PostgreSQL `dacqua_dolce_migrator` vs `dacqua_dolce_app` privilege separation;
- Cloudflare split routing + Proton human/business mail + Postmark application/customer mail + direct Postfix/OpenDKIM observability mail;
- local PostgreSQL backup/restore commissioned;
- AWS S3/restic off-host repository not yet commissioned.

Do not rebuild from obsolete planning assumptions. Follow `docs/production/REBUILD_RUNBOOK.md` and the repository production assets it references.

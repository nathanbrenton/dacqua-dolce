# PT33-A — Reusable Business Provisioning Specification v2

**State:** Draft specification for review; no infrastructure or application change.  
**Source revision:** `50dab782dd3ec4309ee970ddc31977877afcfead`.  
**Source Git status:** `## main...origin/main`.  
**Evidence:** `dacqua-pt33a-current-context.zip`, selected tracked Git files; not a complete application review or host inspection.

## Mission and workflow separation

Three workflows must be supported without conflation:

1. **Disaster recovery:** recover an authorized, existing business, using that same business's validated backup, secret custody and known-good revision. Backup existence and successful restoration are separate gates.
2. **Clean rebuild:** recreate an existing business's infrastructure and software with a *fresh database*; previously stored customer/business transactions do not return.
3. **New business:** provision an independent identity, database, credentials, hostname, sessions, provider resources, backups and staff accounts, starting from approved clean seed data rather than D’Acqua's operational catalog/data.

Design preference: one independently deployed business instance per environment, sharing **source code and generator tooling**, not a multi-tenant customer database. A physical host or PostgreSQL cluster may be shared if runtime identities and data privileges are isolated and resources are budgeted.

## Source-grounded coupling matrix

| Source | Observed coupling | PT33 disposition |
|---|---|---|
| `scripts/production/deploy_release.sh` | APP_ROOT=/srv/dacqua-dolce, ENV_FILE=/etc/dacqua-dolce/backend.env, Turnstile key path, systemd restart, manifest/revision files, DACQUA_* runtime assertions | Parameterize into instance-specific template or compatibility adapter; preserve original |
| `scripts/production/stage_release_rsync.sh` | D’Acqua-specific SSH/stage names and release-manifest conventions | Parameterize into instance-specific template or compatibility adapter; preserve original |
| `infra/production/postgresql/init_database.sh` | hardcoded database dacqua_dolce and roles dacqua_dolce_app/dacqua_dolce_migrator | Parameterize into instance-specific template or compatibility adapter; preserve original |
| `infra/production/systemd/dacqua-dolce-api.service` | dacqua-app identity, paths, unit and writable shared path | Parameterize into instance-specific template or compatibility adapter; preserve original |
| `backend/app/core/config.py` | DACQUA_ prefix; dacqua_session / dacqua_csrf default cookie names; Turnstile hostname and secret fields | Parameterize into instance-specific template or compatibility adapter; preserve original |
| `docs/production/REBUILD_RUNBOOK.md` | existing extensive business-specific disaster-recovery and commissioning instructions | Parameterize into instance-specific template or compatibility adapter; preserve original |
| `infra/production/nginx/dacqua-dolce-https.conf.template` | D’Acqua-specific NGINX host/release configuration to audit before rendering | Parameterize into instance-specific template or compatibility adapter; preserve original |
| `infra/production/backend.env.example` | D’Acqua runtime/provider setting names; secret values must remain outside manifest | Parameterize into instance-specific template or compatibility adapter; preserve original |

Additional audit targets before PT33-B: cookie/CORS/CSRF validation, NGINX upstream and CSP, Postmark stream and sender setup, Cloudflare Turnstile widget/hostname verification, frontend branded metadata/assets and build-time settings, business catalog/seed scripts, tax/payment merchant identities, policy provenance, backup/monitoring labels and alert routing. This context ZIP does **not** contain the full frontend or all business models; those items are not yet source-verified.

## Configuration ownership

- **Committed manifest:** non-secret immutable business/instance identifiers and intended service infrastructure; logical *references* to secrets and external resources only.
- **Secret custody:** per-instance protected `/etc/<instance>` or an approved secret manager. No actual passwords/tokens in Git or generated contexts.
- **Database:** per-business mutable catalog, inventory, quote, return policy, merchandising order and customer history. D’Acqua has a configurable `product_family_order` table; future seed defaults must not override saved ordering on redeploy.
- **Frontend:** renders configured brand/catalog and server-authoritative state, but is never the source of truth for business transactions or permissions.
- **External provider dashboards:** DNS/TLS, Turnstile, Postmark, business mail, payments/tax, and backups have independently commissioned ownership and explicit checklists.
- **Dedicated third-party accounts per business (approved decision, 2026-10-08):** each business must independently own and control its accounts/logins for its domain registrar, hosting provider (including Vultr or another host), Proton or business-mail provider, Postmark, Cloudflare, Better Stack, AWS/storage/backup services, and any future payments/tax/integration providers. Separate credentials within the same provider account are not the approved default. No shared login, API token, recovery address, billing identity, DNS zone, cloud account, backup repository, or provider admin authorization should be silently inherited. Record account owner, recovery procedure, billing responsibility, MFA, least-privilege operator access, and decommission/transfer steps in the per-business commissioning checklist. Do not store credentials or recovery codes in manifests or Git. Where account separation is impossible under a provider's product model, stop for explicit client approval and document the exception before provisioning.

## Manifest invariants

The associated JSON Schema validates a safe base shape, while the future PT33-B planner must enforce **semantic and environmental** constraints:

- `business.id` is stable and does not encode environment; `instance.id` is unique for business+environment; all identifiers use restricted ASCII characters and safe lengths.
- `app.service_user`, systemd unit, paths, DB/roles, ports, NGINX server names, cookie namespace, backup namespace and observability instance labels are unique across cohosted deployments.
- Absolute paths are normalized and checked against symlinks/path traversal **at apply time**, not merely by regex; never write inside another instance's root.
- `network.bind_host` is loopback (`127.0.0.1`) for the supported initial deployment.
- Production public domains must be authorized, HTTPS enforced, and cookie domains host-only by default. Domain, CSRF, CORS, Turnstile hostname and mail sender must be validated together.
- Database runtime and migrator credentials are **different**. Runtime does not own schema or possess privileges on another business's data. Migrator lacks cluster-wide administration privileges.
- No D’Acqua product/customer rows, credentials, Postmark tokens, Turnstile secrets, live payment keys, historical policy records or backup repositories are inherited by new-business mode.
- Manifest `profile` selects a reviewed compatible application type; it does **not** prove the current water-filtration app is business-agnostic. PT33-C must address application-level separation.
- Do not silently default a new business to the D’Acqua mail sender, brand, origin, cookie names, tax/checkout policy or catalog seed. Missing mandatory settings fail closed.
- The proposed model does not introduce a shared multi-tenant users/customers schema.

## Security and isolation model

**Separate trust boundaries:** operator workstation/Git; target host; Unix runtime identity; target DB and migration role; NGINX/TLS; DNS/Turnstile; Postmark and business mailbox; backup provider; observability/reporting endpoints.

**Before apply:** require workflow choice, exact source SHA, authorized target instance, manifest validation, dry-run plan, protected-resource collision checks, secret binding checklist, and verified operator approval. No generic `--force` should bypass protected D’Acqua identities.

**Secret design:** manifest records names like `postmark_token` or `db_runtime_password` as references, never actual values. Site keys are public but still business/domain-bound. Validate provider resource ownership, scopes, mail verification, webhook signature requirements and hostnames during commissioning.

**Database privilege tests:** target runtime role cannot read/modify D’Acqua tables or run DDL; target migrator is limited to its DB. A cross-business authorization failure must block completion.

**Backup separation:** per-instance encryption credential and destination/namespace; tag metadata with business and instance identity. Restore must reject mismatched backup identity, except under a separately audited transfer operation not part of ordinary provisioning.

## Provisioning dependency order

1. **Preflight:** verify clean source/exact revision, business ownership, mode (`disaster_recovery`, `clean_rebuild`, `new_business`), manifest/schema + collision plan.
2. **External prerequisites:** independent domain/DNS, mail/Turnstile/backup identities and provider ownership (record missing commissioning items explicitly).
3. **Host baseline:** Debian security, SSH/nftables, packages, PostgreSQL, capacity and DNS reliability; never weaken existing service policy.
4. **Isolated OS identity/paths:** non-login service user/group; `/srv/<instance>`, `/etc/<instance>`, `/var/lib/<instance>` and stage root with safe permissions.
5. **PostgreSQL identity:** dedicated DB + migrator/runtime roles and least-privilege grants; verify cross-instance access denied.
6. **Secrets and provider binding:** populate protected sinks, never write secrets into release trees or generated artifacts.
7. **Exact-revision stage/build:** verify 40-character Git SHA and manifest hashes, construct immutable backend/frontend releases with correct business-specific public build values.
8. **Database initialization:** DR restores compatible authorized dump *before any intentional upgrade*; clean/new runs migrations and approved seed only. Never mix DR and new-business data paths.
9. **NGINX/systemd and TLS:** render target vhost/upstream/unit/CSP; syntax-check before enabling. Check Turnstile, email-domain auth and host security boundary.
10. **Bootstrap/observability/backups:** fresh authorized admin; per-instance monitoring/alerts; test backup creation and an independent restoration rehearsal.
11. **Acceptance + activation:** verify function/security, record revision/migration head/rollback release; enable public access only after gates pass.

## Backward-compatible migration path

**PT33-A (now):** source-grounded specification only. D’Acqua retains `/srv/dacqua-dolce`, `/etc/dacqua-dolce`, `DACQUA_*` and existing runbooks.

**PT33-B:** build a guarded generator with `validate`, `plan` and `render` modes and deterministic output. No production `apply` by default; no modification of D’Acqua resources. It must plan the actual source paths discovered above.

**PT33-C:** separate brand/catalog, mail/domain, provider bindings, runtime and infrastructure config with a compatibility adapter preserving the live D’Acqua settings.

**PT33-D:** rehearse disposable deployment on independently named resources with clean DB, distinct cookies/ports/secrets and no production customer data; record evidence of restoration and rollback.

**PT33-E:** reconcile the existing 1,158-line D’Acqua rebuild guide against validated general provisioning steps; keep the specific production recovery runbook intact.

Any later migration of D’Acqua into generic templates is a separate approved change, not required for onboarding another business.

## Clean-room acceptance gates

- **Source/revision:** deterministic render; exact SHA/stage validation; no unexpected writes or secrets in diff/archive.
- **Collisions:** duplicate hostname, path, port, Unix name, DB role/name, cookie name, backup namespace and provider account all fail safely.
- **Identity:** service account cannot read another business's secret files; runtime/migrator DB privilege separation verified by negative tests.
- **Data:** new-business users/orders/quotes/history empty, except explicit reviewed bootstrap seed; catalog seed cannot overwrite mutable ordering/policy.
- **Web:** correct host/HTTPS redirects, security headers/CSP, CSRF, cookies/CORS, protected routes, login and target-brand copy.
- **Forms:** Turnstile expected action/hostname, independent provider bindings; server-side validation, abuse controls, controlled transactional email.
- **Commerce:** checkout remains fail-closed until target-specific tax/payment commissioning; never inherit D’Acqua merchant credentials or tax classifications.
- **Operational:** readiness with bounded retries, NGINX routing, alert labels, log secrecy, backups, restore into isolated scratch DB and rollback after simulated failed deploy.
- **Evidence:** record checks and stop reasons, separately distinguish code validation, local smoke, disposable rehearsal and live provider commissioning.

## Review questions before PT33-B

1. Which *application profiles* beyond water-filtration are intended? Separate reusable platform from industry-specific catalog/workflows.
2. Will second businesses share the existing Vultr server initially, or use distinct hosts? Isolation checks must cover both.
3. Which provider resources may be owned by a shared organization but still isolated by business server/account/keys?
4. How will a business-specific clean seed and initial staff/admin account be approved?
5. What resource quotas, monitoring routes and recovery objectives must new instances meet?

**PT33-A does not authorize deploying, modifying, or migrating production.**

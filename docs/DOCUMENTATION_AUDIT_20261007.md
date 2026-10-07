# Documentation Audit — 2026-10-07

This pass reconciles the production/rebuild documentation with the application and infrastructure work completed after the 2026-10-06 audit. It is a current-source/rebuild reconciliation, not a chronological troubleshooting log. Git state and active production release are intentionally treated as separate facts: a newly pushed commit is not called production-commissioned until release metadata/deployment validation confirms it.

## Authority and active-release rule

The active production SHA/release path is operational state and must be read from immutable release metadata/deployment output. It is intentionally not maintained as a long-lived constant in rebuild prose.

The authority model remains:

- Git: source, migrations, deployment assets, repository-managed catalog metadata/images, frontend behavior, and technical documentation;
- Production PostgreSQL: live accounts, orders, quotes, communications, policies, product lifecycle, pricing/inventory, audit/evidence, and other mutable business state;
- protected configuration/provider state: runtime secrets, DNS/mail/TLS/vendor configuration outside Git;
- backups/restic: disaster recovery, not routine environment synchronization.

## Rebuild workflow reconciliation

The rebuild runbook now explicitly collapses historical milestones into one current-source deployment:

1. provision/recover the host and protected configuration;
2. restore authoritative Production PostgreSQL when recovering an existing business;
3. stage one exact 40-character Git revision;
4. run the standard deployment helper;
5. let Alembic apply the full migration chain;
6. let catalog reconciliation apply current seed-owned metadata/variants/images;
7. perform one consolidated current-state browser acceptance pass.

Historical PT releases are not replayed one-by-one.

A blank database is documented as a new-environment path, not production disaster recovery. PT53 policy JSON is not a substitute for restoring Production PostgreSQL.

## 2026-10-07 application changes represented

Documentation now incorporates:

- PT54 formal Order Reviewed checklist, reviewer/timestamp evidence, customer-response hold, fulfillment/Order Confirmed blocking, and no automatic substitution;
- catalog shared `Product Category -> Product Family -> Product Variant` identity used by both cards and detail pages;
- Essence `Automatic Rinse` customer-facing naming and operational retirement of Essence Pass-Through;
- historical Harmony Regenerating retirement with lifecycle state separated from canonical naming;
- Origin `Ultra-Pure` / `Alkaline Plus` differentiation;
- Refine 1.5/2.0 cu ft variants, 1.5 default, and repository-managed supplied images;
- customer-facing select affordance shared across themes and product-detail footer/logo appearance controls;
- residential-use-only catalog warranty direction without invented legal duration/coverage;
- Customer Inbox Website/Email source labeling, non-clickable inbound/customer URLs, and narrow advisory Postmark SpamAssassin/SPF evidence when provider headers exist;
- public support-form CSRF/rate-limit/honeypot controls;
- field-specific FastAPI/Pydantic validation errors for Quote/Inquiry and Support rather than raw `422` fallback;
- optional Cloudflare Turnstile and a dedicated Spam/Quarantine workflow retained as uncommissioned follow-up decisions.

## Infrastructure/rebuild corrections

The rebuild/operations docs now also capture the validated resolver mitigation used after intermittent Vultr resolver failures:

- `/etc/resolv.conf` uses `1.1.1.1` and `8.8.8.8`;
- DHCP is prevented from overwriting resolver state;
- the current host interface is `enp1s0`, but a replacement host must verify its actual interface name before reproducing that boundary.

The existing split communications architecture remains unchanged:

- Cloudflare authoritative DNS/root MX and address-specific routing;
- Proton human/business mail;
- Postmark application/customer transactional mail and inbound email webhook;
- PostgreSQL durable communications archive;
- direct local Postfix/OpenDKIM observability delivery after Vultr TCP/25 approval.

## Files reconciled

Current-state documentation updated in this pass:

- `README.md`
- `docs/CLIENT_NOTES_IMPLEMENTATION_MATRIX.md`
- `docs/EMAIL_AND_PASSWORD_RECOVERY.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/OPERATIONS_AND_PRICING_GOVERNANCE.md`
- `docs/PHONE_DATA_HANDLING.md`
- `docs/PRODUCT_IMAGE_ASSETS.md`
- `docs/OPERATIONS_UI_CONSISTENCY.md`
- `docs/PRODUCTION_HOST_BOOTSTRAP.md`
- `docs/PRODUCTION_HOST_RUNBOOK.md`
- `docs/PRODUCTION_DEPLOYMENT_FOUNDATION.md`
- `docs/production/README.md`
- `docs/production/ARCHITECTURE_OVERVIEW.md`
- `docs/production/COMMUNICATIONS_AND_POSTMARK.md`
- `docs/production/DEPLOYMENT_AND_ROLLBACK.md`
- `docs/production/OPERATIONS_REFERENCE.md`
- `docs/production/PENDING_INTEGRATIONS.md`
- `docs/production/REBUILD_RUNBOOK.md`

Historical milestone records remain historical and are not rewritten merely to make old prose look current.

# D'Acqua Dolce Production Architecture Overview

## 1. Purpose

D'Acqua Dolce is a public water-filtration commerce and customer-lifecycle application. Production is currently deployed as a single-host P0 architecture on Vultr, with strict loopback boundaries around the application, database, and observability services.

The canonical public origin is:

    https://dacquadolce.com

The `www` hostname is an alias and redirects permanently to the canonical bare domain.

This document represents the current production/rebuild architecture through the 2026-10-07 PT54, catalog, Customer Inbox, and public-support hardening work. The active production SHA/release path is operational state and must be read from immutable release metadata/deployment output rather than maintained as a prose constant.

## 2. Production host

| Item | Current production value |
| --- | --- |
| Hostname | `dacqua-platform-prod-01` |
| Provider | Vultr |
| Public IPv4 | `144.202.114.17` |
| Operating system | Debian GNU/Linux 13 (trixie) |
| Snapshot release | Debian 13.7 |
| Architecture | x86-64 |
| Compute | 4 vCPU |
| Memory | ~8 GiB RAM |
| Swap | 8 GiB, retained |
| Root filesystem | ~150 GiB usable filesystem |
| Server timezone | UTC |
| `vm.swappiness` | 10 |

The host is intentionally consolidated for P0. The architecture favors explicit local boundaries, backup/restore validation, and rebuildability over early multi-host complexity.

### Resolver reliability

The current production host does not rely on the intermittently failing Vultr-provided recursive resolvers for application/DNS operations. The validated mitigation keeps `/etc/resolv.conf` on `1.1.1.1` and `8.8.8.8` and prevents DHCP from rewriting it. On the current host the DHCP interface is `enp1s0`; a rebuilt host must verify its actual interface name before reproducing the `dhcpcd` `nohook resolv.conf` boundary.

This is host networking configuration, not application configuration. Validate name resolution after any DHCP/network rebind before continuing a deployment.

## 3. Application stack

### Frontend

- React 19
- TypeScript
- Vite
- production static build served directly by Nginx

The customer account experience includes profile/address management plus site-wide visual-theme and light/dark preferences. The same persisted appearance selection applies to Operations; the current default baseline is Light + Lagoon Editorial unless the user has stored an override. Product-detail pages reuse the customer footer/logo appearance controls, and customer-facing select controls share one theme-safe interactive affordance rather than product-specific styling.

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2
- Alembic
- Uvicorn managed by systemd

The backend listens only on:

    127.0.0.1:8000

The public Nginx edge proxies application API traffic to this listener.

### Identity and account administration

Production identity currently includes:

- customer registration and login;
- secure cookie sessions and CSRF protection;
- password reset using expiring, single-use, hash-only tokens;
- email verification using expiring, single-use, hash-only tokens;
- explicit verification confirmation so ordinary GET/link scanning does not consume the token;
- privileged MFA;
- application roles `customer`, `employee`, `administrator`, and `developer`, with `manager` retained only as a legacy/deprecated enum value for compatibility;
- capability-based authorization: employee Operations + pricing/inventory read, administrator Operations + pricing/inventory write + ordinary account administration, and developer full application authority including Audit Log;
- developer-only Audit Log visibility;
- out-of-band CLI management of `developer`;
- guarded CLI `set-staff-role` migration for replacing all roles on an existing account with exactly one staff role;
- audited privileged identity changes.

Application roles are not PostgreSQL roles. Human/customer identities never receive direct database credentials. Production identities are preserved and migrated in place; the destructive dev fixture/bootstrap workflow is not used in production.

### Catalog

The repository contains a canonical rebuild-grade catalog baseline:

    backend/catalog/production_catalog.json

Repository-managed product media required by that baseline lives under the frontend public product-media tree and therefore travels with the exact Git revision.

The public presentation uses one API-provided structured identity:

    Product Category -> Product Family -> Product Variant

Catalog cards and individual product pages consume the same identity so names cannot drift independently between views. Current source includes the accepted Essence **Automatic Rinse** naming, Origin **Ultra-Pure / Alkaline Plus** differentiation, and Refine 1.5/2.0 cu ft variants with variant-aware images/presentation. Legacy/historical records remain representable without embedding lifecycle words such as `(Retired)` in canonical names.

The catalog seed reconciles seed-owned descriptive metadata and missing canonical variants/images while preserving operational state such as pricing history, inventory, reservations, approved claims, jurisdiction rules, lifecycle/public-retirement state, quote eligibility, and verification state. This is intentional: Git describes the catalog baseline; Production PostgreSQL remains authoritative for live business state.

The deployment helper runs catalog reconciliation after Alembic and before activation. Re-running the same catalog against an already reconciled production database is expected to report zero changes. A blank-database bootstrap is not equivalent to disaster recovery because it cannot reconstruct mutable production state.

### Database

- PostgreSQL 17.11
- database: `dacqua_dolce`
- migration/ownership role: `dacqua_dolce_migrator`
- runtime application role: `dacqua_dolce_app`
- loopback-only listener on `127.0.0.1:5432` and `[::1]:5432`
- SCRAM-SHA-256 password authentication for loopback TCP connections

PostgreSQL is not exposed through the public firewall.

The database privilege boundary separates deployment-time schema authority from runtime application access:

- `dacqua_dolce_migrator` owns the database and application objects and is used by Alembic and deployment-time catalog reconciliation;
- `dacqua_dolce_app` has runtime DML and sequence privileges but does not own application objects and cannot create schema objects;
- neither application-specific login role has superuser, `CREATEDB`, `CREATEROLE`, replication, or `BYPASSRLS` privileges;
- default privileges created under `dacqua_dolce_migrator` grant the runtime role the required access to future Alembic-created tables and sequences.

This limits the database DDL authority available to a compromised web application process.

## 4. Public request flow

    Internet
       |
       | TCP 80 / 443
       v
    Nginx
       |-------------------------------> React/Vite static build
       |
       | /api/* and /health
       v
    FastAPI / Uvicorn
       | 127.0.0.1:8000
       v
    PostgreSQL
       127.0.0.1:5432

Nginx is the only public application edge. TCP 22 is additionally public for administrative SSH.

### Public and internal health surfaces

Public:

    GET https://dacquadolce.com/health
    -> {"status":"ok"}

Internal only:

    GET http://127.0.0.1:8000/readiness
    -> {"status":"ready"}

Public requests to `/readiness` intentionally return Nginx 404. Production API documentation and OpenAPI surfaces are also blocked publicly.

## 5. TLS and HTTP policy

Let's Encrypt/Certbot supplies the certificate for:

- `dacquadolce.com`
- `www.dacquadolce.com`

The production certificate is ECDSA. Nginx permits TLS 1.2 and TLS 1.3 and redirects ordinary HTTP traffic to the canonical HTTPS origin.

The production Nginx edge sets security headers including HSTS, `X-Content-Type-Options`, `X-Frame-Options`, a restrictive Referrer Policy, Permissions Policy, and Content Security Policy.

The public request-body limit is currently 2 MiB.

## 6. Host security boundary

### SSH

Production SSH is key-only:

- root login disabled;
- password authentication disabled;
- keyboard-interactive authentication disabled;
- public-key authentication enabled;
- X11 forwarding disabled.

Human administration uses the non-root production administrator account and `sudo`.

### Firewall

nftables is authoritative. The inbound policy is default-drop.

Public inbound TCP ports:

- 22 — SSH
- 80 — HTTP / ACME / HTTPS redirect
- 443 — HTTPS

PostgreSQL, FastAPI, Grafana, Prometheus, Alertmanager, exporters, Loki, Alloy, and other internal services remain loopback-only and are not opened through nftables.

### Additional baseline controls

- fail2ban protects SSH;
- unattended upgrades are enabled;
- journald is persistent;
- application runtime secrets live outside the release tree;
- the FastAPI unit has a validated hardened systemd sandbox;
- observability-unit sandbox hardening remains an incremental follow-up and must be validated service-by-service rather than assumed complete.

## 7. Release/deployment model

Production uses timestamped releases under:

    /srv/dacqua-dolce/releases/<UTC timestamp>

The active application is selected by:

    /srv/dacqua-dolce/current

which is a symlink to the active release.

Shared runtime state belongs under:

    /srv/dacqua-dolce/shared

Production environment configuration is external to the release tree:

    /etc/dacqua-dolce/backend.env
    /etc/dacqua-dolce/migration.env

`backend.env` contains runtime application configuration and is the only environment file loaded by `dacqua-dolce-api.service`.

`migration.env` contains the separate deploy-time PostgreSQL URL. It is root-only, is sourced by the deployment helper for Alembic/catalog reconciliation, and is never loaded into the FastAPI systemd service.

The FastAPI service runs as the dedicated `dacqua-app` account.

### Release ownership and lifecycle

The hardened deployment workflow:

- creates a timestamped release;
- copies sanitized source into the release with server-side `rsync`;
- installs/builds backend and frontend dependencies;
- creates an on-demand PostgreSQL backup when the commissioned helper is present;
- runs Alembic;
- reconciles the canonical production catalog;
- normalizes successful release trees to `root:root` with no group/other write permission;
- atomically switches `/srv/dacqua-dolce/current`;
- validates local readiness and the public edge;
- automatically restores the previous application release if post-switch validation fails;
- retains the five newest successful timestamped releases by default.

PostgreSQL migrations are never automatically downgraded as part of application rollback. See `DEPLOYMENT_AND_ROLLBACK.md`.

The transport used to place a complete source tree on the production host is
separate from activation. The commissioned staging workflow uses
`scripts/production/stage_release_rsync.sh` to export an exact Git revision,
generate/verify a source manifest, and copy that staged artifact to the
production staging directory. The production copy is independently checked with
`verify_staged_source.py` before activation. Source must never be rsynced
directly into `/srv/dacqua-dolce/current`, and timestamped releases are
immutable.

### Rebuild composition and milestone collapse

A rebuild does **not** replay PT milestones manually. One exact current Git revision carries the accumulated application code, Alembic migration chain, catalog source/media, frontend UX, and security behavior. The production deployment helper then performs build -> pre-migration backup -> `alembic upgrade head` -> catalog reconciliation -> activation/verification.

Production PostgreSQL is a separate authority layer. Restoring the database recovers live accounts, orders, communications, policies, lifecycle state, pricing/inventory, and evidence; deploying the current Git revision brings that restored schema/catalog metadata forward. Protected `/etc` configuration plus external DNS/mail/TLS provider state form the remaining rebuild layers.

This separation is what makes the rebuild efficient: current source is deployed once, while mutable production data is restored rather than reconstructed from historical implementation notes.

## 8. Observability stack

All observability application listeners are local-only.

| Component | Version / role | Listener |
| --- | --- | --- |
| node_exporter | 1.12.1 host/systemd metrics | `127.0.0.1:9100` |
| Prometheus | 3.13.2 metrics and alert evaluation | `127.0.0.1:9090` |
| Blackbox Exporter | 0.26.0 HTTPS probes | `127.0.0.1:9115` |
| Alertmanager | 0.28.1 alert routing | `127.0.0.1:9093` |
| Grafana | 13.2.2 visualization | `127.0.0.1:3000` |
| Loki | 3.7.7 log storage | `127.0.0.1:3100`, gRPC `127.0.0.1:9096` |
| Alloy | 1.19.2 journald/log pipeline | `127.0.0.1:12345` |
| Monit | 5.34.3 host/service checks | Unix socket only |

Prometheus is configured for 180 days of time retention with a 10 GiB size cap. The operational requirement is to preserve at least 90 days of useful metric history; retention/capacity should be revisited from measured ingestion and disk growth rather than relying permanently on an undersized fixed cap. Loki retains selected production logs for 7 days.

Alloy reads journald, relabels selected production units, and sends the resulting stream to Loki. Grafana is provisioned with Prometheus and Loki data sources and three repo-managed production dashboards.

Monit independently checks host resources, critical systemd services, and the local FastAPI readiness endpoint.

### Alert coverage

Prometheus rules cover, among other conditions:

- scrape target failure including Alloy;
- public HTTPS probe failure;
- TLS certificate expiration;
- critical systemd service failure, including Monit and database backup/restore jobs;
- local readiness health-check failure/overdue state;
- root disk and inode pressure;
- memory pressure;
- active swap pressure;
- OOM-killer activity;
- high/critical CPU utilization;
- PostgreSQL backup and restore-check timer health/freshness.

Operational acceptance requires zero firing/pending production alerts attributable to the release and zero failed systemd units; verify the live state rather than relying on a historical checkpoint.

## 9. External monitoring

Better Stack provides independent public checks for:

1. `https://dacquadolce.com`
2. `https://dacquadolce.com/health`
3. `https://www.dacquadolce.com`

`/readiness` is deliberately not externally monitored because it is an internal-only endpoint.

Daily and weekly Better Stack heartbeat resources have been created. Direct observability report delivery is commissioned; heartbeat submission remains a separate pending step and must be tied only to confirmed successful report delivery.

## 10. Reporting

The production observability report generator is:

    /usr/local/sbin/dacqua-observability-report.py

Direct observability-mail delivery is commissioned as of 2026-10-01. Vultr outbound TCP/25 was approved and connectivity validated, forward/reverse DNS was aligned at `mailout.dacquadolce.com`, Postfix/OpenDKIM was configured for outbound-only local submission, and a controlled daily report was received before timers were enabled.

Commissioned schedule:

- daily — `dacqua-observability-daily-report.timer`, 09:00 `America/Los_Angeles` to `nathan@nathanbrenton.com`;
- weekly — `dacqua-observability-weekly-report.timer`, Saturday 11:00 `America/Los_Angeles` to `nathan@nathanbrenton.com`, `jamie.dacqua.dolce@gmail.com`, and `dacquadolce@proton.me`.

The monitoring transport is:

    report generator
      -> local send wrapper
      -> Postfix (127.0.0.1:25 only)
      -> OpenDKIM (127.0.0.1:8891)
      -> recipient MX

This remains separate from Postmark application mail so routine status traffic does not consume the limited Postmark allowance. Better Stack report-delivery heartbeat submission remains pending.

## 11. Backup and recovery model

### Commissioned local database protection

Production currently performs PostgreSQL custom-format logical backups to:

    /var/backups/dacqua-dolce/postgresql/

Each completed `.dump` has a SHA-256 checksum. The backup job validates that `pg_restore` can read the archive before finalizing it.

A second job performs a real restore into a disposable local validation database and verifies that application relations exist before removing the scratch database.

Schedule:

- daily backup — 03:15 `America/Los_Angeles`
- weekly full restore validation — Sunday 04:15 `America/Los_Angeles`

Local backup retention is 30 days. The application deployment workflow also creates an on-demand pre-migration backup before Alembic when the commissioned backup helper is available.

### Restic / off-host disaster recovery

Restic is installed/prepared and the repository encryption password has been stored securely on and off the server. The off-host S3 repository has **not** been provisioned yet.

Local backup/restore validation is commissioned; off-host disaster recovery remains pending.

## 12. Email and communications boundary

### Authoritative DNS and public inbound routing — commissioned

The registrar remains Moniker, while authoritative DNS is hosted by Cloudflare. The current assigned authoritative nameservers are:

    carrera.ns.cloudflare.com
    earl.ns.cloudflare.com

The production web records remain **DNS only**, so HTTP/HTTPS traffic still goes directly to the Vultr/Nginx origin rather than through Cloudflare's reverse proxy. Cloudflare is used here for authoritative DNS and free Email Routing.

Public customer correspondence enters through:

    external sender
      -> support@dacquadolce.com
      -> Cloudflare Email Routing
      -> private Postmark inbound destination
      -> Postmark Default Inbound Stream
      -> authenticated HTTPS webhook
      -> FastAPI
      -> PostgreSQL communications archive

Catch-all mail routing is disabled. The private Postmark destination is intentionally omitted from documentation and employee UI.

Cloudflare remains the root-domain MX/front-door. Current inbound MX hosts are `route1.mx.cloudflare.net`, `route2.mx.cloudflare.net`, and `route3.mx.cloudflare.net`. Proton's requested MX records are intentionally not installed because Cloudflare must route different local parts to different downstream systems.

The current single root SPF policy is:

    v=spf1 ip4:144.202.114.17 include:_spf.mx.cloudflare.net include:_spf.protonmail.ch ~all

Proton DKIM uses the three selectors `protonmail`, `protonmail2`, and `protonmail3`; their provider-generated CNAME targets must be retrieved from Proton during rebuild rather than hard-coded. DMARC is published as:

    v=DMARC1; p=none

`p=none` is deliberate monitoring/commissioning mode. Hardening to `quarantine` or `reject` is a future explicit security change after every legitimate sender is validated.

Postmark retains its independent sending-domain DKIM and custom Return-Path CNAME at `pm-bounces.dacquadolce.com`.

Direct infrastructure mail uses:

- `mailout.dacquadolce.com` A -> `144.202.114.17` (DNS only);
- PTR `144.202.114.17` -> `mailout.dacquadolce.com`;
- DKIM selector `infra2026._domainkey.dacquadolce.com`;
- visible/envelope sender `monitoring@dacquadolce.com`;
- Cloudflare route `monitoring@dacquadolce.com -> dacquadolce@proton.me` for inbound replies/bounces.


### Human/business email — commissioned

Proton Mail Essentials hosts human/business mail while Cloudflare remains the inbound routing boundary.

Current validated human route:

    external sender
      -> jamie@dacquadolce.com
      -> Cloudflare Email Routing
      -> dacquadolce@proton.me
      -> Proton mailbox

Outbound Proton mail can use `jamie@dacquadolce.com` as the visible From identity. Inbound and outbound acceptance passed on 2026-09-30. The provider-native `dacquadolce@proton.me` identity remains the Proton organizational/bootstrap/recovery identity.

### Application transactional email — commissioned

FastAPI sends transactional mail through the Postmark HTTPS API. Direct outbound TCP/25 is not required for application/customer email.

Account/security mail uses the transactional no-reply sender. Employee customer-service replies choose from approved company sender roles. Quote-request replies prefer `sales`, then `contact`, `info`, `support`, and `no-reply`; other replies prefer `support`, then `contact`, `info`, `sales`, and `no-reply`. The authenticated staff user remains the internal author/audit actor.

### Durable communications archive — commissioned

PostgreSQL stores durable threads, messages, recipients, attachments, and normalized events in the `communication_*` tables. The older `email_deliveries` table remains a transport/status ledger rather than the correspondence store.

Authentication/recovery secrets may be delivered live but are redacted in the durable archive when required.

### Postmark inbound processing — commissioned

The public webhook is:

    POST /api/webhooks/postmark/inbound

It is protected with HTTP Basic authentication from protected runtime configuration. The exact Nginx path has a 64 MiB request envelope while the ordinary site remains 2 MiB. Provider MessageID uniqueness provides retry-safe idempotency.

Thread resolution prefers a Postmark `MailboxHash` thread UUID, then RFC `In-Reply-To`, then creates a new thread. A real production provider retry was validated without creating a duplicate archived message.

### Employee Customer Inbox and threaded replies — commissioned

Authenticated Operations users can:

- search Inbox/System/Archived/All conversations;
- keep structured application-generated verification/reset/welcome mail under System rather than the normal customer Inbox;
- archive/restore threads without deleting durable records;
- inspect a selected conversation with independent vertical scrolling;
- reply in the same durable thread;
- see explicit failed-delivery provenance when associated failure data exists.

Employee reply path:

    Operations UI
      -> FastAPI
      -> PostgreSQL archive
      -> Postmark HTTPS API
      -> customer

A private thread-specific Postmark alias is used only as `Reply-To`, allowing the customer's normal Reply action to return to the same conversation. A production three-message acceptance sequence (`inbound -> outbound -> inbound`) was validated.

The inbox renders archived plain-text message bodies. Inbound and customer-supplied URLs are intentionally non-clickable to reduce accidental phishing interaction; outbound/archive URLs may be linkified where appropriate. Arbitrary inbound HTML is not trusted/rendered as executable markup. Message source is surfaced as Website/Email/provider-aware evidence, and genuine Postmark inbound events may expose normalized SpamAssassin/SPF fields when those headers were actually archived. Website form submissions are a separate `provider=web` source and never fabricate email-authentication evidence.

### Address roles

Current commissioned application sender roles:

- `sales@dacquadolce.com`;
- `contact@dacquadolce.com`;
- `info@dacquadolce.com`;
- `support@dacquadolce.com`;
- `no-reply@dacquadolce.com`.

`support@dacquadolce.com` remains the public inbound Customer Inbox address. These application role addresses are **mail identities**, not application UAM accounts. Human custom-domain mail is a separate Proton/Cloudflare concern: `jamie@dacquadolce.com` is currently commissioned as a named human/business identity routed by Cloudflare to the Proton organization mailbox. Additional named human identities require explicit provisioning.

The visible delivery display name is `D'Acqua Dolce`; the PostgreSQL archive retains the canonical bare sender address. The private thread-aware Postmark inbound alias is used only as `Reply-To`.

### Observability reports — commissioned direct delivery

The application Postmark path remains separate from `/usr/local/sbin/dacqua-observability-report.py`. The infrastructure-report path was commissioned on 2026-10-01 using direct local Postfix/OpenDKIM delivery after Vultr TCP/25 approval, aligned forward/PTR DNS, SPF authorization, DKIM publication, and a successful controlled daily report.

The wrapper is `/usr/local/sbin/dacqua-observability-send-report`. Daily and weekly systemd timers are enabled and active at the documented PT schedules. Better Stack report-delivery heartbeat submission remains uncommissioned until it is explicitly connected to successful delivery.

## 12.1 Current application/commerce and policy authority

The current rebuild target includes the PT36-PT54 governance layers: versioned return policies and exceptions; safe account retirement; pricing promotions; inventory lifecycle; Supplier Confirmed order lifecycle; back-in-stock notifications; manufacturer-claim provenance and warranty support; automated-tax and payment-provider commissioning foundations; explicit launch phases and Commerce Launch Gate; employee-controlled Order Confirmed mail; discontinued-product retirement/replacements; formal-quote staff review; internal installer candidates; launch-dependency evidence tracking; accessibility hardening; policy portability; and the PT54 formal Order Reviewed checklist/customer-response hold boundary. Current source also includes the accepted catalog shared-identity/variant reconciliation and the Customer Inbox/public-support hardening described in the communications runbook.

The data authority model is intentionally split:

- Git is authoritative for code, schema/migrations, deployment assets, and the canonical catalog source.
- Production PostgreSQL is authoritative for live accounts, orders, communications, pricing/inventory state, evidence records, and approved customer policies.
- PT53 policy bundles are explicit transport artifacts. They do not replace Production PostgreSQL as the live source of truth.
- A recommended non-production refresh is Production `Export all` -> trusted JSON bundle -> Local/Dev/Test import preview -> lifecycle-preserving import only where `DACQUA_POLICY_IMPORT_ALLOW_LIFECYCLE_PRESERVATION=true`. Do not enable that flag in Production.
- AWS S3/Restic, once commissioned, is a disaster-recovery copy of production backup state, not a Local/Dev/Test synchronization source.

## 13. Production boundaries represented by the current rebuild target

Commissioned:

- Vultr/Debian host baseline;
- SSH hardening, nftables, fail2ban, unattended upgrades, persistent journald;
- PostgreSQL 17 local database with separated migrator/runtime roles;
- Nginx + TLS + canonical redirect and public security headers;
- React/FastAPI production release lifecycle with immutable releases, automatic application rollback, and retention;
- canonical production catalog bootstrap/reconciliation;
- customer registration/login/password reset/email verification;
- privileged MFA and account-role administration;
- customer profile/address and account appearance controls;
- Postmark transactional application email;
- durable PostgreSQL communications archive;
- authenticated Postmark inbound webhook with attachment/event archival and idempotent retry handling;
- local health/readiness checks;
- full local observability stack;
- repo-managed Grafana dashboards;
- Better Stack public monitors;
- local PostgreSQL backup and real restore validation;
- restic client-side encryption preparation;
- PT46 Commerce Launch Gate and PT51 external dependency evidence registry;
- PT47 employee-controlled `Order Confirmed` communication;
- PT48 discontinued-product retirement/replacement workflow;
- PT49 formal-quote staff-review gate;
- PT50 internal-only installer candidate registry;
- PT53 policy export/import portability;
- PT54 formal Order Reviewed checklist and customer-response hold workflow;
- shared catalog Category/Family/Variant identity plus accepted Essence/Origin/Refine reconciliation and repository-managed Refine variant media;
- Customer Inbox Website/Email source labeling, inbound-link hardening, and advisory Postmark spam/SPF evidence when provider headers exist.

Current repository/rebuild target also includes the public support-form CSRF/rate-limit/honeypot controls and field-specific structured validation messages. Confirm the active release metadata before treating a newly committed source behavior as production-commissioned.

Not yet commissioned:

- off-host AWS S3/restic repository and off-host restore rehearsal;
- Better Stack report-delivery heartbeat submission (direct report email/timers are already commissioned);
- explicit communications retention/purge policy, including attachment and backup lifecycle;
- remaining observability service systemd hardening beyond the already hardened FastAPI service;
- live automated-tax production commissioning;
- exact Affinity24 gateway discovery and concrete production payment adapter/checkout;
- coordinated attorney review of customer-facing legal policies;
- shipping-insurance provider/legal/claims commissioning;
- public support phone publication after the authoritative number is supplied;
- customer-facing installer/referral program pending legal review;
- public transactional launch.

### FastAPI systemd sandbox

The production FastAPI process runs as the dedicated unprivileged `dacqua-app:dacqua-app` identity. The application release itself is immutable to that identity; its designated writable application path is:

    /srv/dacqua-dolce/shared

The API systemd unit applies the following production sandboxing controls in addition to its existing `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`, `ProtectHome`, restricted address families, `LockPersonality`, and `MemoryDenyWriteExecute` controls:

- `UMask=0027`;
- `PrivateDevices=true`;
- protection for the clock, kernel tunables, kernel modules, kernel logs, control groups, and hostname;
- `RestrictSUIDSGID=true`;
- `RestrictRealtime=true`;
- `RemoveIPC=true`;
- `SystemCallArchitectures=native`;
- an empty capability bounding set and no ambient capabilities.

The API needs no Linux capabilities because Uvicorn binds only to the unprivileged loopback port `8000`.

Release directories are deployment artifacts, not mutable application state. Production releases are expected to be owned by `root:root` and must not be writable by `dacqua-app`. The hardened deployment lifecycle normalizes this ownership during deployment.

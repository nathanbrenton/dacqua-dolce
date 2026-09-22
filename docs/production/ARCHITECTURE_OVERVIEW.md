# D'Acqua Dolce Production Architecture Overview

## 1. Purpose

D'Acqua Dolce is a public water-filtration commerce and customer-lifecycle application. Production is currently deployed as a single-host P0 architecture on Vultr, with strict loopback boundaries around the application, database, and observability services.

The canonical public origin is:

    https://dacquadolce.com

The `www` hostname is an alias and redirects permanently to the canonical bare domain.

This document represents the validated production state through 2026-09-22.

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

## 3. Application stack

### Frontend

- React 19
- TypeScript
- Vite
- production static build served directly by Nginx

The customer account experience includes profile/address management, visual-theme selection, and a persistent light/dark preference. Operations keeps its own persistent appearance preference and defaults to dark when no preference has previously been stored.

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
- roles `customer`, `employee`, `manager`, `administrator`, and `developer`;
- web administration of `employee`, `manager`, and `administrator` by administrator/developer accounts;
- CLI-only management of the `developer` role;
- audit events for privileged identity changes.

### Catalog

The repository contains a canonical rebuild-grade public catalog baseline:

    backend/catalog/production_catalog.json

The catalog seed reconciles seed-owned descriptive metadata while preserving operational state such as pricing history, inventory, reservations, approved claims, jurisdiction rules, lifecycle flags, and verification state.

The deployment helper runs the catalog reconciliation after Alembic and before activation. Re-running the same catalog against an already reconciled production database is expected to report zero changes.

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

The transport used to place a complete source tree on the production host is separate from activation. Through the 2026-09-22 checkpoint, exact Git commits were exported with `git archive` and transferred with `scp`. Future deployments may use an rsync-based exact-commit staging cache to reduce transfer volume, but the source still must represent a known commit and must never be rsynced directly into `/srv/dacqua-dolce/current`.

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

At the 2026-09-22 production checkpoint there were no firing or pending Prometheus alerts and no failed systemd units.

## 9. External monitoring

Better Stack provides independent public checks for:

1. `https://dacquadolce.com`
2. `https://dacquadolce.com/health`
3. `https://www.dacquadolce.com`

`/readiness` is deliberately not externally monitored because it is an internal-only endpoint.

Daily and weekly Better Stack heartbeat resources have been created, but heartbeat submission remains tied to completion of the observability report-delivery workflow.

## 10. Reporting

The production observability report generator is:

    /usr/local/sbin/dacqua-observability-report.py

Dry-run report generation has been validated. Report timers remain intentionally disabled until real report delivery is implemented and validated.

Desired schedule after commissioning:

- daily — 09:00 `America/Los_Angeles` to `nathan@nathanbrenton.com`;
- weekly — Saturday 11:00 `America/Los_Angeles` to `nathan@nathanbrenton.com` and `jamie.dacqua.dolce@gmail.com`.

Recipient declarations should remain obvious in protected report configuration. Application Postmark delivery is already commissioned; the remaining work is specifically the observability-report sender/timer path, not general application email approval.

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

### Application transactional email — commissioned

FastAPI sends transactional application email through the Postmark HTTPS API. The production Postmark server token is stored outside Git in the protected application environment.

The `dacquadolce.com` sending domain is verified and live delivery was validated on 2026-09-22. Production verification/password-recovery/quote notification paths have been exercised successfully.

Direct outbound TCP/25 from the Vultr host remains blocked. This does not affect the Postmark HTTPS API and does not require a local Postfix-to-MX architecture.

`email_deliveries` remains the transport metadata ledger. It stores delivery metadata, provider references, and bounded error information rather than complete correspondence bodies.

### Durable communications archive — commissioned

The application now has a dedicated PostgreSQL communications archive:

    communication_threads
    communication_messages
    communication_recipients
    communication_attachments
    communication_events

The schema was introduced by Alembic revision `c41b7e2a9d63` and is owned by `dacqua_dolce_migrator`; the runtime role `dacqua_dolce_app` has the required CRUD privileges.

Outbound transactional email is archived through this model. Sensitive authentication values are redacted in the archive copy where required while the live outbound message still contains the value needed by the recipient.

### Postmark inbound processing — commissioned

Inbound architecture:

    external sender
        -> Postmark inbound processing
        -> HTTPS /api/webhooks/postmark/inbound
        -> Nginx
        -> FastAPI
        -> PostgreSQL communications archive

The webhook uses HTTP Basic authentication with credentials held only in protected runtime configuration. The exact webhook path is the only browser-CSRF exemption for this machine-to-machine integration.

Nginx preserves the normal 2 MiB site request-body limit and grants only the exact inbound webhook a 64 MiB envelope for Postmark JSON/base64 attachment transport.

Inbound Postmark `MessageID` is the idempotency key. Duplicate/retried webhook delivery resolves to the existing archived message rather than creating a duplicate.

Inbound thread matching attempts:

1. Postmark `MailboxHash` -> existing communication thread UUID;
2. RFC `In-Reply-To` -> prior archived internet Message-ID;
3. otherwise a new thread.

A real Gmail -> Postmark -> production webhook -> PostgreSQL message was validated on 2026-09-22. Provider retries resulted in one archived database message for the provider MessageID.

The full implementation/rebuild boundary is documented in `COMMUNICATIONS_AND_POSTMARK.md`.

### Employee inbox/reply workflow — pending

The durable archive and inbound transport are commissioned, but the authenticated employee shared-inbox list/detail/reply experience is not yet commissioned.

The intended reply path is:

    employee -> authenticated Operations UI -> FastAPI
             -> PostgreSQL archive -> Postmark HTTPS API

A general-purpose IMAP/Dovecot mailbox on the production host is not required for this application design.

### Observability reports — pending delivery

The application Postmark path being live does not automatically commission the separate `/usr/local/sbin/dacqua-observability-report.py` delivery/timer workflow. That remains pending until its Postmark integration, recipients, timers, failure handling, and heartbeats are validated.

## 13. Production boundaries at PT12

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
- restic client-side encryption preparation.

Not yet commissioned:

- off-host AWS S3/restic repository and off-host restore rehearsal;
- observability report email delivery/timers and corresponding Better Stack report heartbeats;
- employee shared-inbox/reply workflow and explicit communications retention policy;
- remaining observability service systemd hardening beyond the already hardened FastAPI service;
- payment-provider checkout;

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

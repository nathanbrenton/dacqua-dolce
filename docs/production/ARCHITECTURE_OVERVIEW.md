# D'Acqua Dolce Production Architecture Overview

## 1. Purpose

D'Acqua Dolce is a public water-filtration commerce and customer-lifecycle application. Production is
currently deployed as a single-host P0 architecture on Vultr, with strict loopback boundaries around the
application, database, and observability services.

The canonical public origin is:

    https://dacquadolce.com

The `www` hostname is an alias and redirects permanently to the canonical bare domain.

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
| Root filesystem | ~150 GiB usable filesystem in the PT10 snapshot |
| Server timezone | UTC |
| `vm.swappiness` | 10 |

The host is intentionally small and consolidated for P0. The architecture favors explicit local boundaries
and rebuildability over early multi-host complexity.

## 3. Application stack

### Frontend

- React 19
- TypeScript
- Vite
- production static build served directly by Nginx

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

### Database

- PostgreSQL 17.11
- database: `dacqua_dolce`
- application role: `dacqua_dolce_app`
- loopback-only listener on `127.0.0.1:5432` and `[::1]:5432`

PostgreSQL is not exposed through the public firewall.

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

Public requests to `/readiness` intentionally return Nginx 404. Production API documentation and OpenAPI
surfaces are also blocked publicly.

## 5. TLS and HTTP policy

Let's Encrypt/Certbot supplies the certificate for:

- `dacquadolce.com`
- `www.dacquadolce.com`

The PT10 certificate is ECDSA. Nginx permits TLS 1.2 and TLS 1.3 and redirects ordinary HTTP traffic to the
canonical HTTPS origin.

The production Nginx edge sets security headers including HSTS, `X-Content-Type-Options`,
`X-Frame-Options`, a restrictive Referrer Policy, Permissions Policy, and Content Security Policy.

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

PostgreSQL, FastAPI, Grafana, Prometheus, Alertmanager, exporters, Loki, Alloy, and other internal services
remain loopback-only and are not opened through nftables.

### Additional baseline controls

- fail2ban protects SSH;
- unattended upgrades are enabled;
- journald is persistent;
- systemd services use sandboxing controls where appropriate;
- application runtime secrets live outside the release tree.

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

The FastAPI service runs as the dedicated `dacqua-app` account.

### Current PT10 release

    /srv/dacqua-dolce/releases/20260917T084102Z

The PT10 snapshot shows this release owned by the administrator account rather than normalized root ownership.
That is a known deployment-lifecycle hardening item and must be resolved in the dedicated deployment milestone;
it is not treated here as the desired long-term release-ownership policy.

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

Prometheus retains metrics for 180 days with a 10 GiB size cap. Loki retains selected production logs for
7 days.

Alloy reads journald, relabels selected production units, and sends the resulting stream to Loki. Grafana is
provisioned with Prometheus and Loki data sources.

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

At the PT10 checkpoint there were no firing or pending Prometheus alerts and no failed systemd units.

## 9. External monitoring

Better Stack provides independent public checks for:

1. `https://dacquadolce.com`
2. `https://dacquadolce.com/health`
3. `https://www.dacquadolce.com`

`/readiness` is deliberately not externally monitored because it is an internal-only endpoint.

Daily and weekly Better Stack heartbeat resources have been created, but heartbeat submission remains tied to
completion of the report-email delivery workflow.

## 10. Reporting

The production observability report generator is:

    /usr/local/sbin/dacqua-observability-report.py

Daily and weekly dry-run report generation has been validated. Report timers are intentionally not enabled
until the final email-delivery architecture is commissioned.

Desired schedule after commissioning:

- daily — 09:00 `America/Los_Angeles`
- weekly — Saturday 11:00 `America/Los_Angeles`

## 11. Backup and recovery model

### Commissioned local database protection

Production currently performs PostgreSQL custom-format logical backups to:

    /var/backups/dacqua-dolce/postgresql/

Each completed `.dump` has a SHA-256 checksum. The backup job validates that `pg_restore` can read the archive
before finalizing it.

A second job performs a real restore into a disposable local validation database and verifies that application
relations exist before removing the scratch database.

Schedule:

- daily backup — 03:15 `America/Los_Angeles`
- weekly full restore validation — Sunday 04:15 `America/Los_Angeles`

Local backup retention is 30 days.

### Restic / off-host disaster recovery

Restic is installed/prepared and the repository encryption password has been stored securely on and off the
server. The off-host S3 repository has **not** been provisioned yet.

Local backup is therefore commissioned; off-host disaster recovery remains pending.

## 12. Email boundary

Application/report mail is intended to submit through a local Postfix interface so applications remain
provider-agnostic and gain durable queueing/retry/logging.

Direct outbound TCP/25 from this host is blocked by the provider. The final authenticated relay or hosted-mail
architecture has not yet been commissioned.

Postmark remains a candidate for application transactional mail, but it is not the foundational host-mail path
at PT10 and the account approval state previously prevented live Gmail delivery.

Do not treat mail delivery or report timers as commissioned until the corresponding production validation is
completed.

## 13. Production boundaries at PT10

Commissioned:

- Vultr/Debian host baseline;
- SSH hardening, nftables, fail2ban, unattended upgrades, persistent journald;
- PostgreSQL 17 local database;
- Nginx + TLS + canonical redirect;
- React/FastAPI production release;
- local health/readiness checks;
- full local observability stack;
- Better Stack public monitors;
- local PostgreSQL backup and real restore validation;
- restic client-side encryption preparation.

Not yet commissioned:

- off-host S3/restic repository;
- final Postfix outbound delivery/relay architecture;
- live report-email delivery and report timers;
- Better Stack report heartbeats tied to successful mail submission;
- final provisioned Grafana dashboard set;
- deployment ownership/automatic rollback hardening.

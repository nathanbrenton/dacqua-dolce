# D'Acqua Dolce Production Rebuild Runbook

## Status and scope

This is the authoritative PT12 rebuild baseline for `dacqua-platform-prod-01`, validated through 2026-09-22.

It documents the clean validated production architecture and the repository-supported rebuild path. It does
not record commissioning mistakes, failed experiments, or transient troubleshooting.

A fully reproducible rebuild requires two classes of material:

1. repository-controlled application/infrastructure assets; and
2. protected production-only configuration and credentials that are deliberately not stored in Git.

Several later integrations remain intentionally uncommissioned and are listed in `PENDING_INTEGRATIONS.md`.
Do not invent them during a rebuild.

## 1. Target state

Rebuild target:

- Vultr VM;
- Debian GNU/Linux 13 (trixie), x86-64;
- hostname `dacqua-platform-prod-01`;
- 4 vCPU;
- ~8 GiB RAM;
- ~160 GB provider disk / ~150 GiB root filesystem;
- 8 GiB swap;
- UTC system timezone;
- `vm.swappiness=10`;
- canonical public origin `https://dacquadolce.com`;
- alias `https://www.dacquadolce.com` redirecting to canonical.

## 2. Required protected material

Before destroying/rebuilding a production host, confirm independent access to:

- administrator SSH private key;
- populated `/etc/dacqua-dolce/backend.env` values or an authoritative secret-store copy;
- PostgreSQL application credential;
- MFA/application cryptographic material;
- TLS/DNS administrative access;
- Better Stack account/monitor configuration;
- backup encryption password;
- Postmark production server token or an authoritative secret-store copy;
- observability-reporting Postmark token/configuration if that workflow has been commissioned;
- future AWS/S3 credentials only after that integration is commissioned.

Never place these values in Git or this runbook.

## 3. Repository assets used for rebuild

Current repository production assets include:

    infra/production/host/
    infra/production/nginx/
    infra/production/postgresql/
    infra/production/systemd/
    scripts/production/

Relevant application deployment documentation and dependency policy also live under `docs/`.

The production documentation in this directory supersedes older bootstrap/planning documents when they
conflict with the current validated production state.

## 4. Provision the host

Create the Vultr VM with the target resources and Debian 13.

Record provider recovery-console access before SSH hardening.

Set the production hostname:

    dacqua-platform-prod-01

The public IPv4 at the 2026-09-22 checkpoint is `144.202.114.17`; DNS must be verified against the actual rebuilt host rather than
blindly reusing an old address.

## 5. Base Debian bootstrap

Use the repository host bootstrap assets rather than reconstructing package choices from memory:

    infra/production/host/bootstrap_debian13.sh

The base host must ultimately provide at least:

- administrator tooling;
- Python/runtime prerequisites required by the application release;
- Nginx;
- PostgreSQL 17;
- Certbot;
- nftables;
- fail2ban;
- unattended upgrades;
- persistent journald;
- systemd.

After installation, set/verify:

- UTC timezone;
- 8 GiB swap;
- `vm.swappiness=10`.

## 6. Create the administrator account

Use:

    infra/production/host/create_admin_user.sh

or the repository's current equivalent helper.

Install only the administrator's public SSH key. Do not copy private workstation keys onto the host.

Prove a second key-authenticated SSH session works before disabling root/password SSH.

## 7. Configure nftables

Use the repository baseline under:

    infra/production/host/nftables.conf

Validated inbound policy:

- default-drop;
- accept established/related traffic;
- accept loopback;
- permit ICMP/ICMPv6;
- permit required DHCP traffic;
- permit new TCP connections only on 22, 80, and 443.

Verify:

    sudo nft list ruleset

Do not open 5432, 8000, 3000, 3100, 9090, 9093, 9096, 9100, 9115, 12345, or Monit TCP access publicly.

## 8. Configure fail2ban

Use the repository fail2ban installer/configuration under:

    infra/production/host/

Verify:

    sudo fail2ban-client status
    sudo fail2ban-client status sshd

## 9. Harden SSH

Use the repository SSH hardening assets under:

    infra/production/host/

Validated effective requirements include:

- `PermitRootLogin no`;
- `PasswordAuthentication no`;
- `KbdInteractiveAuthentication no`;
- `PubkeyAuthentication yes`;
- `X11Forwarding no`;
- `MaxAuthTries 3`.

Keep the original session open while proving a new hardened login.

## 10. Configure persistent system logging and unattended upgrades

Persistent journald and unattended upgrades are part of the production baseline. Verify both after rebuild:

    journalctl --disk-usage
    systemctl status unattended-upgrades --no-pager --full
    systemctl list-timers --all --no-pager | grep -E 'apt-daily|logrotate'

## 11. Install and configure PostgreSQL 17

The validated database boundary is local-only:

    listen_addresses = 'localhost'
    port = 5432

Repository configuration assets:

    infra/production/postgresql/postgresql-local.conf
    infra/production/postgresql/pg_hba-dacqua.conf
    infra/production/postgresql/init_database.sh

Create:

- database `dacqua_dolce`;
- login role `dacqua_dolce_migrator`;
- login role `dacqua_dolce_app`;
- database and application-object ownership assigned to
  `dacqua_dolce_migrator`;
- runtime DML/sequence access assigned to `dacqua_dolce_app`;
- no schema `CREATE` privilege for `dacqua_dolce_app`;
- no superuser, create-database, create-role, replication, or bypass-RLS
  privileges for either application-specific login role.

`dacqua_dolce_migrator` is the deploy-time DDL/Alembic identity.
`dacqua_dolce_app` is the runtime web-application identity.

The bootstrap configures default privileges for objects created by
`dacqua_dolce_migrator` so future Alembic-created tables and sequences
automatically receive the runtime privileges required by
`dacqua_dolce_app`.

Supply both database passwords only through protected process/environment
boundaries while initializing the database. Do not write either populated
credential into the repository.

Verify:

    sudo -u postgres psql -Atqc "SHOW server_version;"
    sudo -u postgres psql -Atqc "SHOW listen_addresses;"
    sudo -u postgres psql -Atqc "SHOW port;"

Expected major version is PostgreSQL 17 and the listener must remain local-only.

## 12. Prepare production filesystem and runtime identity

Required model:

    /srv/dacqua-dolce/
      current -> /srv/dacqua-dolce/releases/<release>
      releases/
      shared/

    /etc/dacqua-dolce/
      backend.env
      migration.env

`backend.env` should be owned by `root:dacqua-app` and readable by the
application service without being world-readable.

`migration.env` must be owned by `root:root`, mode `0600`, and must never be
loaded by the FastAPI systemd service.

The API runs as dedicated service account:

    dacqua-app

The populated environment file must remain outside the release tree and protected from unprivileged users.

Successful application releases are normalized to `root:root` ownership and have group/other write permission removed
before activation. `/srv/dacqua-dolce/current` is changed only through an atomic symlink replacement.

## 13. Install production environment configuration

Start from:

    infra/production/backend.env.example
    infra/production/migration.env.example

Install populated production copies at:

    /etc/dacqua-dolce/backend.env
    /etc/dacqua-dolce/migration.env

Required boundaries:

- `backend.env`: runtime configuration, readable by `dacqua-app`;
- `migration.env`: deploy-only database URL, `root:root`, mode `0600`;
- `dacqua-dolce-api.service` loads only `backend.env`;
- `deploy_release.sh` sources `migration.env` for Alembic and deployment-time catalog reconciliation, then removes `DACQUA_MIGRATION_DATABASE_URL` from its environment before activation.

Never commit either populated production file.

The application currently has configuration namespaces for environment/database/session/CSRF/MFA/security,
public origin, email provider/from/operator destination, Postmark token, password-reset TTL, and email
verification TTL. Document names, never secret values.

## 14. Configure Nginx HTTP/ACME edge

Repository templates live under:

    infra/production/nginx/

The HTTP server block must:

- listen on IPv4/IPv6 port 80;
- serve `/.well-known/acme-challenge/` from the ACME webroot;
- redirect ordinary requests to `https://dacquadolce.com$request_uri`.

Validate before reload:

    sudo nginx -t

## 15. Issue TLS certificate

Use Certbot/Let's Encrypt for both production names:

- `dacquadolce.com`;
- `www.dacquadolce.com`.

The current certificate path model is:

    /etc/letsencrypt/live/dacquadolce.com/fullchain.pem
    /etc/letsencrypt/live/dacquadolce.com/privkey.pem

Do not copy private-key material into the repository.

Verify renewal timer:

    systemctl list-timers --all --no-pager | grep certbot

## 16. Enable production HTTPS edge

The validated Nginx behavior must include:

- TLS 1.2/1.3;
- canonical redirect from `www` to bare domain;
- static frontend root `/srv/dacqua-dolce/current/frontend/dist`;
- `/health` proxied to FastAPI;
- `/api/` proxied to FastAPI;
- `/readiness` blocked publicly with 404;
- `/docs` and `/docs/` descendants blocked publicly with 404;
- `/redoc` and `/redoc/` descendants blocked publicly with 404;
- `/api/docs` and `/api/docs/` descendants blocked publicly with 404;
- `/api/redoc` and `/api/redoc/` descendants blocked publicly with 404;
- `/openapi.json` blocked publicly with 404;
- `/api/openapi.json` blocked publicly with 404;
- SPA fallback to `/index.html`;
- immutable one-year caching for built `/assets/`;
- 2 MiB request-body limit;
- production security headers.

Validate:

    sudo nginx -t
    sudo systemctl reload nginx

## 17. Install application systemd units

Repository application units live under:

    infra/production/systemd/

Required API properties include:

- user/group `dacqua-app`;
- working directory `/srv/dacqua-dolce/current/backend`;
- environment file `/etc/dacqua-dolce/backend.env`;
- loopback Uvicorn listener on port 8000;
- restart on failure;
- systemd sandboxing controls;
- write access restricted to `/srv/dacqua-dolce/shared` where applicable.

Also install the local readiness one-shot service and one-minute timer.

## 18. Deploy application release

Repository helper:

    scripts/production/deploy_release.sh

The hardened deployment sequence is:

1. validate source tree, production environment, and retention policy;
2. capture the previously active release;
3. create a timestamped release directory and copy sanitized source with server-side `rsync`;
4. create the backend virtual environment and install the constrained runtime package;
5. run frontend `npm ci` and `npm run build`;
6. create an on-demand PostgreSQL backup when the commissioned backup helper is available;
7. run `alembic upgrade head`;
8. run `./.venv/bin/python -m app.cli.seed_catalog apply` using the deploy-time database authority;
9. remove the deploy-only migration URL from the process environment;
10. normalize release ownership to `root:root` and remove group/other write permission;
11. atomically switch `/srv/dacqua-dolce/current`;
12. restart `dacqua-dolce-api.service`;
13. require local `/readiness` and public release verification;
14. automatically restore the previous application release if post-switch validation fails;
15. after success, retain the newest five timestamped releases by default.

The release source must represent a known Git revision. Through the 2026-09-22 checkpoint the validated staging method was exact `git archive` + SHA-256 + `scp` + extraction. An rsync-based exact-revision staging cache is planned to reduce workstation-to-server transfer volume; do not rsync directly into `/srv/dacqua-dolce/current` or mutate a timestamped release in place.

Database migrations are not automatically downgraded during application rollback. Migration sequencing must preserve
compatibility with the immediately previous application release unless a deployment has an explicit database recovery
plan. See `docs/production/DEPLOYMENT_AND_ROLLBACK.md`.

## 19. Verify application edge

Local:

    curl -fsS http://127.0.0.1:8000/readiness

Public:

    curl -fsS https://dacquadolce.com/health

Also verify:

- canonical redirect from `www`;
- public `/readiness` -> 404;
- public `/api/docs` -> 404;
- public `/openapi.json` -> 404.

Use the repository verifier when applicable:

    scripts/production/verify_release.sh https://dacquadolce.com

## 20. Configure and validate DNS, Cloudflare Email Routing, Postmark, and customer communications

Application outbound/inbound communications are commissioned through Cloudflare authoritative DNS + Email Routing, Postmark transport/inbound processing, and the PostgreSQL communications archive.

Detailed technical procedure:

    docs/production/COMMUNICATIONS_AND_POSTMARK.md

### 20.1 Understand the service boundaries

- **Registrar:** owns the domain registration/delegation. D'Acqua Dolce currently uses Moniker.
- **Authoritative DNS:** publishes the DNS zone. D'Acqua Dolce currently uses Cloudflare.
- **Cloudflare Email Routing:** receives mail for public custom-domain addresses and forwards selected addresses to verified destinations. It is not a human mailbox.
- **Postmark:** sends application email through HTTPS and converts inbound mail sent to its private inbound destination into webhook requests.
- **FastAPI/PostgreSQL:** provide the authenticated employee Customer Inbox and durable archive.

Keeping these roles separate makes the design portable: another company can replace the registrar, DNS provider, or transport provider without changing the conceptual boundaries.

### 20.2 Configure outbound application email

Populate only the protected runtime environment:

    DACQUA_PUBLIC_ORIGIN=https://dacquadolce.com
    DACQUA_EMAIL_PROVIDER=postmark
    DACQUA_POSTMARK_SERVER_TOKEN=<secret>
    DACQUA_EMAIL_FROM=<verified-no-reply-sender>
    DACQUA_EMAIL_SUPPORT_FROM=support@dacquadolce.com
    DACQUA_EMAIL_OPERATOR_TO=<business-operator-address>

Never place populated tokens or credentials in Git, documentation, screenshots, tickets, or shell history. Direct TCP/25 is not required.

### 20.3 Confirm communications schema

The communications schema was introduced by Alembic revision:

    c41b7e2a9d63

Expected tables:

    communication_threads
    communication_messages
    communication_recipients
    communication_attachments
    communication_events

Expected owner/runtime roles:

    owner/migrator: dacqua_dolce_migrator
    runtime:        dacqua_dolce_app

### 20.4 Provision and validate the Postmark inbound webhook

Generate strong Basic Auth values in `/etc/dacqua-dolce/backend.env`:

    DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME
    DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD

Validate over loopback and public HTTPS:

    wrong/missing Basic Auth -> HTTP 401
    valid Basic Auth + {}    -> HTTP 422

Install the canonical Nginx template. Only `/api/webhooks/postmark/inbound` receives the 64 MiB envelope; the ordinary site remains 2 MiB.

Configure Postmark's Default Inbound Stream webhook privately and use Postmark **Check**. Do not record the complete authenticated URL or private Postmark inbound address.

### 20.5 Rebuild authoritative DNS safely

Before changing registrar nameservers, create/import the complete Cloudflare zone and verify at minimum:

- apex web `A` record;
- `www` alias;
- Postmark custom Return-Path CNAME;
- Postmark DKIM TXT selector/value;
- any other production verification/CAA/DMARC records that exist at rebuild time.

For D'Acqua Dolce at this checkpoint:

    A      @            -> 144.202.114.17       DNS only
    CNAME  www          -> dacquadolce.com      DNS only
    CNAME  pm-bounces   -> pm.mtasv.net         DNS only
    TXT    20260917171819pm._domainkey          Postmark-generated DKIM value

Use the provider-generated DKIM value from Postmark; do not copy an obsolete key from prose.

Change registrar delegation only after the zone is complete. Current D'Acqua Dolce Cloudflare nameservers are:

    carrera.ns.cloudflare.com
    earl.ns.cloudflare.com

For a new company/domain, use the nameservers Cloudflare actually assigns. DNSSEC should remain disabled during a nameserver migration unless the old/new DS/DNSSEC handoff has been explicitly planned; enable it later as a separate validated security change.

After delegation, verify authoritative/public DNS and public HTTPS before enabling mail routing.

### 20.6 Enable Cloudflare Email Routing

Use Cloudflare's Email Routing onboarding so the provider creates its current root MX/SPF/DKIM records.

Definitions:

- **MX:** inbound mail-exchanger destination records;
- **SPF:** sender-policy TXT record;
- **DKIM:** cryptographic signing record identified by a selector;
- **TTL:** resolver cache lifetime.

Do not remove the separate Postmark DKIM selector or Postmark Return-Path CNAME. Different selectors/providers can coexist when serving different purposes.

Add the private Postmark inbound address as a Cloudflare destination and complete the destination verification message through the Customer Inbox. Keep the destination value out of documentation.

Create:

    support@dacquadolce.com -> verified private Postmark inbound destination

Keep catch-all disabled unless the business explicitly wants arbitrary local parts accepted.

### 20.7 Perform public inbound acceptance

Send one controlled external message to:

    support@dacquadolce.com

Verify the message appears as a new inbound conversation in Operations -> Customer Inbox. This validates:

    public address -> Cloudflare -> Postmark -> webhook -> PostgreSQL -> Operations UI

Use metadata-oriented diagnostics and avoid printing the private Postmark destination, verification tokens, complete provider IDs, customer bodies, or attachment bytes.

### 20.8 Validate threaded employee replies

When reply plumbing has materially changed, send one employee reply from Customer Inbox, then answer it using the customer's normal Reply action. The return message should enter the same durable communication thread.

Employee replies visibly originate from `support@dacquadolce.com`; the private thread-specific Postmark alias is used only as `Reply-To`.

Routine releases that do not change communications transport do not need another live-email acceptance test.

### 20.9 Security/privacy/storage boundary

The communications archive contains durable message bodies and may contain attachment bytes. Treat it as sensitive application data.

Do not:

- log full inbound payloads;
- dump message bodies into tickets/chat;
- expose the private Postmark inbound destination;
- expose webhook credentials;
- store unnecessary duplicate raw provider payloads.

Customer Inbox Archive/Restore is a workflow state, not deletion. Define a formal retention/purge policy before adding permanent deletion, especially for attachment bytes and backup copies.

## 21. Install observability stack

Validated production components:

- node_exporter 1.12.1;
- Prometheus 3.13.2;
- Blackbox Exporter 0.26.0;
- Alertmanager 0.28.1;
- Grafana 13.2.2;
- Loki 3.7.7;
- Alloy 1.19.2;
- Monit 5.34.3.

All network listeners remain on loopback. Monit uses its Unix socket only.

Prometheus configuration lives under:

    /etc/prometheus/
    /etc/prometheus/rules/

Current retention:

    time: 180d
    size: 10GB

Loki retention is 7 days.

Grafana data sources for Prometheus and Loki are provisioned from `/etc/grafana/provisioning/`.

### Rebuild-detail boundary

The PT12 state capture proves the validated service locations, listeners, runtime configuration, and health, but the
repository does not yet contain a complete installer/pinning manifest for every observability binary/package.
Do not invent download URLs or checksums. Before calling this runbook fully standalone, capture the validated
installation source/version/checksum/package procedure for each manually installed observability component and
store those assets or instructions under repository-controlled production infrastructure documentation.

The FastAPI unit has separately validated sandbox hardening. Do not assume identical hardening is safe for Grafana/Loki/Prometheus/Alertmanager/exporter vendor units; continue that work service-by-service and record only settings that survive restart/functional validation.

## 22. Validate Prometheus and monitoring

Before restarting Prometheus:

    sudo /usr/local/bin/promtool check config /etc/prometheus/prometheus.yml
    sudo /usr/local/bin/promtool check rules /etc/prometheus/rules/*.yml

Then verify:

    curl -fsS http://127.0.0.1:9090/-/ready
    curl -fsS http://127.0.0.1:9090/api/v1/alerts | python3 -m json.tool

The expected healthy state is no firing/pending alerts and zero failed systemd units.

## 23. Configure Better Stack

External monitors currently cover:

- canonical website;
- public `/health`;
- `www` alias.

Do not externally monitor `/readiness`.

Daily/weekly heartbeat resources exist, but heartbeat submission is not commissioned until the dedicated observability report-delivery path is validated. Application transactional Postmark email is already commissioned; report delivery remains a separate boundary.

## 24. Install local PostgreSQL backup and restore validation

Scripts:

    /usr/local/sbin/dacqua-postgres-backup
    /usr/local/sbin/dacqua-postgres-restore-check

Backup directory:

    /var/backups/dacqua-dolce/postgresql

Required ownership/mode:

- directory owned by `postgres:postgres`;
- mode 0700;
- backup files mode 0600 through restrictive umask.

Backup behavior:

- custom-format `pg_dump`;
- compression;
- `pg_restore --list` validation;
- atomic finalization from temporary file;
- SHA-256 sidecar;
- 30-day local retention.

Restore-check behavior:

- validate checksum;
- create disposable `dacqua_dolce_restore_verify` database;
- restore latest dump with `pg_restore --exit-on-error`;
- confirm application relations exist;
- always remove the scratch database.

Install/enable timers:

- `dacqua-postgres-backup.timer` — daily 03:15 `America/Los_Angeles`;
- `dacqua-postgres-restore-check.timer` — Sunday 04:15 `America/Los_Angeles`.

Verify both manually through their systemd services before relying on the timers.

## 25. Prepare restic

Restic is the selected off-host encryption/snapshot layer.

Protected namespace:

    /etc/dacqua-backup/

The repository password file must remain root-controlled, mode 0600, and have an independent off-server copy.

At PT12, stop here. Do not initialize a fictional remote repository. AWS S3 provisioning is a later milestone.

## 26. Final baseline validation

Run at minimum:

    systemctl --failed --no-pager
    ss -ltnp
    sudo nft list ruleset
    sudo fail2ban-client status sshd
    sudo nginx -t
    sudo certbot certificates
    curl -fsS http://127.0.0.1:8000/readiness
    curl -fsS https://dacquadolce.com/health
    curl -fsS http://127.0.0.1:9090/-/ready
    systemctl list-timers --all --no-pager
    sudo -u postgres ls -lh /var/backups/dacqua-dolce/postgresql/

Expected boundaries:

- only TCP 22/80/443 public;
- PostgreSQL and all observability services local-only;
- application local readiness succeeds;
- public health succeeds;
- Prometheus ready;
- no failed systemd units;
- backup/restore timers active.

## 27. Disaster-recovery boundary

At PT12, loss of the entire Vultr server is not yet fully protected by an off-host commissioned repository.
The local backup/restore system is validated, and restic encryption preparation is complete, but AWS S3 remains
pending.

After off-host backup is commissioned, this runbook must be extended with a tested clean-host restore sequence
that starts from the remote encrypted repository and results in a validated production database/application.

## Grafana dashboard provisioning

Grafana data sources must already be provisioned before installing the D'Acqua
Dolce production dashboards. The Prometheus datasource UID is:

    prometheus

The repository contains:

    observability/grafana/provisioning/dashboards/dacqua-dolce.yaml
    observability/grafana/dashboards/production-overview.json
    observability/grafana/dashboards/host-resources.json
    observability/grafana/dashboards/service-backup-health.json

Before installation, validate the repository definitions:

    python3 scripts/production/validate_grafana_dashboards.py

### Install the repo-managed production dashboards

From a staged copy of the repository on the production server:

    sudo ./scripts/production/install_grafana_dashboards.sh /path/to/staged/repository

The installer:

- validates the source dashboards;
- verifies the existing Prometheus datasource UID;
- backs up prior D'Acqua Dolce Grafana provisioning;
- installs the file provider and three dashboard JSON files;
- restarts Grafana;
- confirms Grafana health;
- confirms Grafana remains bound to `127.0.0.1:3000`;
- verifies all three dashboard UIDs in Grafana 13 unified storage;
- restores the prior managed provisioning if post-install validation fails.

Installed paths:

    /etc/grafana/provisioning/dashboards/dacqua-dolce.yaml
    /var/lib/grafana/dashboards/dacqua-dolce/

Expected dashboard UIDs:

    dacqua-prod-overview
    dacqua-host-resources
    dacqua-service-backup

On the validated production implementation, Grafana 13 stores current
dashboard resources through unified storage. The legacy `dashboard` SQL table
is not the authoritative validation source.

After installation validate:

    systemctl is-active grafana-server
    curl -fsS http://127.0.0.1:3000/api/health
    ss -lntp | grep '127.0.0.1:3000'
    sudo journalctl -u grafana-server --since '-15 minutes' --no-pager -p warning

Also confirm:

- all dashboard PromQL expressions execute successfully against the local
  Prometheus instance;
- all three expected dashboard UIDs exist in unified storage;
- Prometheus has no unexpected firing or pending alerts;
- `systemctl --failed` reports no failed units.

Full dashboard operational documentation is in:

    docs/production/GRAFANA_DASHBOARDS.md

### Validate API sandboxing

Install the canonical API unit from:

    infra/production/systemd/dacqua-dolce-api.service

After installing or changing the unit:

    sudo systemctl daemon-reload
    sudo systemctl restart dacqua-dolce-api.service

Validate without using an interactive pager:

    systemctl is-active dacqua-dolce-api.service
    systemctl status dacqua-dolce-api.service --no-pager --full -n 20
    curl -fsS http://127.0.0.1:8000/readiness
    curl -fsS https://dacquadolce.com/health

The effective production sandbox should include:

    UMask=0027
    PrivateDevices=yes
    ProtectClock=yes
    ProtectKernelTunables=yes
    ProtectKernelModules=yes
    ProtectKernelLogs=yes
    ProtectControlGroups=yes
    ProtectHostname=yes
    RestrictSUIDSGID=yes
    RestrictRealtime=yes
    RemoveIPC=yes
    SystemCallArchitectures=native
    CapabilityBoundingSet=
    AmbientCapabilities=

The release pointed to by `/srv/dacqua-dolce/current` should be owned by
`root:root`, and `dacqua-app` must not be able to write to the release tree.
Application state that requires persistence belongs under explicitly managed
shared/state paths rather than inside a timestamped release.

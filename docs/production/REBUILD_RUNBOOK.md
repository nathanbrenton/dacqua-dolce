# D'Acqua Dolce Production Rebuild Runbook

## Status and scope

This is the authoritative rebuild baseline for the current D'Acqua Dolce production architecture. Application state is reconciled through the PT53 deployment on 2026-10-06; PT47-PT51 browser acceptance is complete, while PT52/PT53 final production browser acceptance remains pending at this audit checkpoint.

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
- TLS/DNS/Cloudflare administrative access;
- Proton organization access/recovery material through the approved password-manager/recovery process;
- Better Stack account/monitor configuration;
- backup encryption password;
- Postmark production server token or an authoritative secret-store copy;
- observability/reporting configuration if that workflow has been commissioned; the intended direct Postfix path does not reuse the application Postmark token;
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

The currently documented production IPv4 is `144.202.114.17`; DNS must be verified against the actual rebuilt host rather than
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

The release source must represent a known Git revision. The commissioned
staging workflow is:

    ./scripts/production/stage_release_rsync.sh \
      REVISION_SHA \
      n8@dacqua-prod

The helper exports only the requested Git revision, generates a verified source
manifest, rsyncs the staged artifact to the production staging directory, and
verifies the remote copy. Independently check
`.dacqua-release-revision`/`verify_staged_source.py` before deployment.

Do not rsync directly into `/srv/dacqua-dolce/current` and never mutate a
timestamped release in place.

Database migrations are not automatically downgraded during application rollback. Migration sequencing must preserve
compatibility with the immediately previous application release unless a deployment has an explicit database recovery
plan. See `docs/production/DEPLOYMENT_AND_ROLLBACK.md`.


## 18.1 Preserve and migrate production application identities

Production UAM is not rebuilt from development fixtures.

Before any identity-affecting release or role migration:

1. take a fresh PostgreSQL backup and validate restore capability;
2. list existing application users and role assignments;
3. inspect linked customer/business records for any account being changed;
4. preserve legitimate users, credentials, MFA state, communications, and audit
   history;
5. deploy the application release without running the dev user bootstrap or
   destructive local database rebuild;
6. verify user/communications counts after deployment;
7. perform only the intended in-place role mutation.

Developer provisioning and deliberate staff-only conversion use the
out-of-band role CLI. For a target that must become exactly one staff role:

    backend/.venv/bin/python3 \
      scripts/manage_user_role.py \
      set-staff-role \
      --email "existing-user@example.com" \
      --role developer \
      --confirm-replace-all-roles

The command replaces all existing application roles on that user, emits an
audit event, rejects legacy `manager`, and protects the final active developer.

Do not hard-delete/recreate a production account merely to normalize roles when
an audited in-place migration is sufficient.

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

## 20. Configure and validate DNS, Cloudflare Email Routing, Proton, Postmark, and communications

D'Acqua Dolce deliberately separates three mail responsibilities:

1. **human/business mail** — Proton Mail Essentials;
2. **application/customer transactional mail and Customer Inbox** — Postmark + the D'Acqua Dolce application/PostgreSQL;
3. **infrastructure monitoring/status mail** — commissioned local Postfix/OpenDKIM direct delivery using `monitoring@dacquadolce.com` and `mailout.dacquadolce.com`.

Cloudflare remains authoritative DNS **and** the root-domain MX/front-door so it can route individual addresses to different downstream systems.

Detailed technical procedure:

    docs/production/COMMUNICATIONS_AND_POSTMARK.md

### 20.1 Understand the service boundaries

- **Registrar:** owns the domain registration/delegation. D'Acqua Dolce currently uses Moniker.
- **Cloudflare authoritative DNS:** publishes the DNS zone.
- **Cloudflare Email Routing:** owns the current root MX path and forwards selected addresses to verified downstream destinations.
- **Proton Mail Essentials:** hosts human/business correspondence and custom-domain sending identities. `dacquadolce@proton.me` remains the organization/bootstrap/recovery identity; `jamie@dacquadolce.com` is the commissioned named business identity.
- **Postmark:** sends application transactional/customer mail through HTTPS and converts inbound mail sent to its private inbound destination into webhook requests.
- **FastAPI/PostgreSQL:** provide the authenticated employee Customer Inbox and durable application correspondence archive.
- **Postfix/OpenDKIM:** local outbound-only MTA/signing path for infrastructure/status reports; Postfix listens only on loopback and is not the public inbound MX.

Do not collapse these roles simply because a vendor setup wizard prefers to control all mail for the domain.

### 20.2 Configure outbound application email

Populate only the protected runtime environment:

    DACQUA_PUBLIC_ORIGIN=https://dacquadolce.com
    DACQUA_EMAIL_PROVIDER=postmark
    DACQUA_POSTMARK_SERVER_TOKEN=<secret>
    DACQUA_POSTMARK_INBOUND_ADDRESS=<private-provider-address>
    DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME=<secret>
    DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD=<secret>
    DACQUA_EMAIL_FROM=no-reply@dacquadolce.com
    DACQUA_EMAIL_SUPPORT_FROM=support@dacquadolce.com
    DACQUA_EMAIL_REPLY_FROM_ADDRESSES=sales@dacquadolce.com,contact@dacquadolce.com,info@dacquadolce.com,support@dacquadolce.com
    DACQUA_EMAIL_SENDER_NAME="D'Acqua Dolce"
    DACQUA_EMAIL_OPERATOR_TO=<business-operator-address>
    DACQUA_PASSWORD_RESET_TTL_MINUTES=30
    DACQUA_EMAIL_VERIFICATION_TTL_MINUTES=1440

Never place populated tokens, private inbound addresses, or credentials in Git, documentation, screenshots, tickets, or shell history. Postmark application delivery uses HTTPS and does not require TCP/25.

The approved `sales@`, `contact@`, `info@`, `support@`, and `no-reply@` addresses are application mail identities. They do not require matching application users or hosted human mailboxes.

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

### 20.5 Restore Proton Business/custom-domain state

Restore access to the Proton organization using the provider-native identity:

    dacquadolce@proton.me

D'Acqua Dolce uses Proton Mail Essentials. Add/verify `dacquadolce.com` using the current Proton-provided ownership-verification record.

Preserve/create the named human/business address:

    jamie@dacquadolce.com

Do not remove `dacquadolce@proton.me`; it remains useful as the organizational/bootstrap/recovery identity.

Obtain the current Proton DKIM values from:

    Proton -> Settings -> Domain names -> dacquadolce.com -> DKIM

The selectors are:

    protonmail._domainkey
    protonmail2._domainkey
    protonmail3._domainkey

The long CNAME targets are provider-generated and must not be copied blindly from old prose.

**Do not add Proton MX records under the current architecture.** Proton may show MX red/unconfigured. That is intentional because Cloudflare owns the domain MX/front-door and performs address-specific routing.

### 20.6 Rebuild authoritative DNS safely

Before changing registrar nameservers, create/import the complete Cloudflare zone and verify at minimum:

- apex web `A` record;
- `www` alias;
- Cloudflare Email Routing MX records;
- Cloudflare Email Routing provider-managed DKIM record/selector when present;
- exactly one root SPF record;
- `_dmarc` TXT record;
- Proton ownership-verification record when required;
- the three Proton DKIM CNAME selectors;
- Postmark custom Return-Path CNAME;
- current Postmark DKIM selector/value;
- any other current production CAA/verification records.

Current non-secret D'Acqua Dolce mail records/policies:

    MX     @     route1.mx.cloudflare.net
    MX     @     route2.mx.cloudflare.net
    MX     @     route3.mx.cloudflare.net
    A      mailout     144.202.114.17
    TXT    @     v=spf1 ip4:144.202.114.17 include:_spf.mx.cloudflare.net include:_spf.protonmail.ch ~all
    TXT    _dmarc     v=DMARC1; p=none
    CNAME  protonmail._domainkey     <current Proton-generated target>
    CNAME  protonmail2._domainkey    <current Proton-generated target>
    CNAME  protonmail3._domainkey    <current Proton-generated target>
    CNAME  pm-bounces                pm.mtasv.net
    TXT    <current Postmark DKIM selector>    <current Postmark-generated DKIM value>
    TXT    infra2026._domainkey    <public key matching the restored/generated direct-mail private key>

There must be only **one** root SPF TXT policy. Reconcile future legitimate senders into that policy instead of adding a second SPF record.

DMARC `p=none` is deliberate commissioning/monitoring mode. Do not automatically change it to `quarantine`/`reject` until all legitimate sending paths are verified for alignment.

Cloudflare may normalize/remove a trailing dot from Proton CNAME targets; that is normal.

Change registrar delegation only after the zone is complete. Current D'Acqua Dolce Cloudflare nameservers are:

    carrera.ns.cloudflare.com
    earl.ns.cloudflare.com

For a new company/domain, use the nameservers Cloudflare actually assigns. DNSSEC should remain disabled during a nameserver migration unless the old/new DS/DNSSEC handoff has been explicitly planned; enable it later as a separate validated security change.

### 20.7 Restore Cloudflare split Email Routing

Cloudflare must remain the root MX provider. Do not replace its MX records with Proton MX records.

Verify/create the human/business routes:

    jamie@dacquadolce.com
      -> dacquadolce@proton.me

    monitoring@dacquadolce.com
      -> dacquadolce@proton.me

Verify the private Postmark inbound destination as a Cloudflare destination without recording its value in Git/docs, then verify/create:

    support@dacquadolce.com
      -> verified private Postmark inbound destination

Keep catch-all disabled.

### 20.8 Perform human/business mail acceptance

Validate inbound:

    external sender
      -> jamie@dacquadolce.com
      -> Cloudflare
      -> dacquadolce@proton.me
      -> Proton Inbox

Validate outbound from Proton with:

    From: jamie@dacquadolce.com

to a controlled external recipient.

When performing authentication acceptance, inspect the received message's current SPF/DKIM/DMARC results. Do not treat Proton's MX-red indicator as an outage under this architecture.

### 20.9 Perform application/customer inbound acceptance

Send one controlled external message to:

    support@dacquadolce.com

Verify the message appears as a new inbound conversation in Operations -> Customer Inbox. This validates:

    public address -> Cloudflare -> Postmark -> webhook -> PostgreSQL -> Operations UI

Use metadata-oriented diagnostics and avoid printing the private Postmark destination, verification tokens, complete provider IDs, customer bodies, or attachment bytes.

### 20.10 Validate threaded employee replies

When reply plumbing has materially changed, send one employee reply from Customer Inbox, then answer it using the customer's normal Reply action. The return message should enter the same durable communication thread.

Employee replies use approved company sender roles. Quote-request replies prefer `sales -> contact -> info -> support -> no-reply`; other replies prefer `support -> contact -> info -> sales -> no-reply`. The private thread-specific Postmark alias is used only as `Reply-To`.

Routine releases that do not change communications transport do not need another live-email acceptance test.

### 20.11 Security/privacy/storage boundary

The communications archive contains durable message bodies and may contain attachment bytes. Treat it as sensitive application data.

Do not:

- log full inbound payloads;
- dump message bodies into tickets/chat;
- expose the private Postmark inbound destination;
- expose webhook credentials;
- store unnecessary duplicate raw provider payloads;
- publish Proton/Postmark secrets;
- assume a provider wizard's preferred MX architecture overrides the documented split-routing design.

Customer Inbox Archive/Restore is a workflow state, not deletion. Define a formal retention/purge policy before adding permanent deletion, especially for attachment bytes and backup copies.

### 20.12 Restore direct infrastructure-monitoring email

The commissioned production path is:

    observability report
      -> /usr/local/sbin/dacqua-observability-send-report
      -> local Postfix
      -> OpenDKIM
      -> recipient MX

Canonical non-secret settings:

- visible/envelope sender: `monitoring@dacquadolce.com`;
- Postfix `myhostname` / SMTP HELO: `mailout.dacquadolce.com`;
- `mailout.dacquadolce.com` A -> `144.202.114.17`;
- PTR `144.202.114.17` -> `mailout.dacquadolce.com`;
- Postfix `inet_interfaces = loopback-only`;
- Postfix `inet_protocols = ipv4`;
- Postfix `mydestination = $myhostname, localhost.$mydomain, localhost`;
- Postfix `relayhost =` empty for direct recipient-MX delivery;
- OpenDKIM selector `infra2026`;
- OpenDKIM local milter on `127.0.0.1:8891`;
- Postfix `milter_default_action = accept`;
- direct-mail private key under `/etc/opendkim/keys/dacquadolce.com/`;
- report configuration under `/etc/dacqua-observability/reporting.env`.

The private DKIM key is secret material. If an authoritative secure backup of the matching private key is unavailable during rebuild, generate a fresh selector/key pair and publish the new public TXT record instead of reusing the old public selector with no matching key.

Restore/install:

- Postfix;
- OpenDKIM + tools;
- `/usr/local/sbin/dacqua-observability-report.py`;
- `/usr/local/sbin/dacqua-observability-send-report`;
- `dacqua-observability-daily-report.service/.timer`;
- `dacqua-observability-weekly-report.service/.timer`.

Do not enable the report timers until all of these pass:

1. outbound TCP/25 connectivity to an actual recipient MX;
2. forward/PTR identity alignment;
3. SPF authorization for the selected envelope domain;
4. OpenDKIM public/private key validation;
5. Postfix/OpenDKIM active with only loopback listeners for local submission/milter;
6. one controlled report is received successfully and authentication results are inspected;
7. Postfix queue returns clean.

Then enable:

    dacqua-observability-daily-report.timer
    dacqua-observability-weekly-report.timer

Canonical schedules:

- daily — 09:00 `America/Los_Angeles` -> `nathan@nathanbrenton.com`;
- weekly — Saturday 11:00 `America/Los_Angeles` -> `nathan@nathanbrenton.com`, `jamie.dacqua.dolce@gmail.com`, `dacquadolce@proton.me`.

Better Stack successful-delivery heartbeat submission remains a separate commissioning step. Do not submit a success heartbeat merely because the report rendered.


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

The current validated state capture proves the validated service locations, listeners, runtime configuration, and health, but the
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

Daily/weekly heartbeat resources exist, but heartbeat submission is not yet commissioned. Application transactional Postmark email and the separate local Postfix/OpenDKIM report-delivery path are both commissioned; heartbeat success must be wired only after confirmed report delivery.

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

At the current checkpoint, stop here. Do not initialize a fictional remote repository. AWS S3 provisioning is a later milestone.

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

At the current checkpoint, loss of the entire Vultr server is not yet fully protected by an off-host commissioned repository.
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


## Policy-state recovery and non-production synchronization

Approved customer policy versions are production PostgreSQL data. They are recovered with the production database, not reconstructed from Git or `production_catalog.json`. PT53 JSON export/import is for deliberate portability and test-environment synchronization, not for replacing database restore during disaster recovery.

For Local/Dev/Test refreshes, export all policy versions from Production and import after preview. Lifecycle-preserving import requires `DACQUA_POLICY_IMPORT_ALLOW_LIFECYCLE_PRESERVATION=true` only in the non-production destination. Keep that setting disabled in Production.

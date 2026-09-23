# D'Acqua Dolce Communications and Postmark Production Runbook

## Purpose

This document is the technical source of truth for the commissioned D'Acqua Dolce application-email and customer-correspondence boundary.

It describes the validated final implementation only. It intentionally omits transient troubleshooting, failed commands, incorrect diagnostics, temporary test assumptions, and superseded implementation paths.

Production validation checkpoint:

- date: 2026-09-22;
- exact deployed source revisions are recorded by immutable release metadata/deployment history rather than treated as configuration constants in this runbook;
- Postmark transactional sending: commissioned;
- PostgreSQL communications archive: commissioned;
- authenticated Postmark inbound webhook: commissioned;
- authenticated Operations Customer Inbox and threaded employee replies: commissioned;
- public `support@dacquadolce.com` inbound routing through Cloudflare Email Routing: commissioned;
- real public-address acceptance (`support@` -> Cloudflare -> Postmark -> webhook -> Customer Inbox): validated.

## 1. Architecture

Application transactional mail:

    FastAPI
      -> durable PostgreSQL communication archive
      -> Postmark HTTPS API
      -> recipient mail system

Public inbound customer mail:

    sender
      -> support@dacquadolce.com
      -> Cloudflare Email Routing
      -> private Postmark inbound destination
      -> Postmark Default Inbound Stream
      -> HTTPS POST /api/webhooks/postmark/inbound
      -> Nginx
      -> FastAPI
      -> PostgreSQL communications archive

Employee replies follow the reverse application path:

    Operations Customer Inbox
      -> FastAPI
      -> PostgreSQL archive
      -> Postmark HTTPS API
      -> customer

The visible sender for employee customer-service replies is `support@dacquadolce.com`. A thread-specific private Postmark inbound alias is used only as `Reply-To` so a customer's normal Reply action returns to the same archived conversation.

Cloudflare is authoritative for DNS, but the production web `A`/`CNAME` records are intentionally **DNS only**. Cloudflare is therefore providing authoritative DNS and inbound Email Routing without acting as the HTTP reverse proxy for the site at this checkpoint.

The production server does not need a general-purpose SMTP/IMAP mailbox stack for this workflow. Direct outbound TCP/25 remains blocked by the hosting provider and is not required by the Postmark HTTPS API path.

### Email/DNS terminology

- **DNS (Domain Name System):** translates domain names into service-routing records.
- **Authoritative nameserver:** the DNS server whose zone data is the source of truth for a domain. The current authoritative provider is Cloudflare.
- **MX (Mail Exchanger):** DNS records that tell other mail systems where inbound mail for a domain should be delivered.
- **SPF (Sender Policy Framework):** a DNS TXT policy describing which infrastructure is permitted to send mail for a domain/envelope domain.
- **DKIM (DomainKeys Identified Mail):** cryptographic signing that lets recipients verify that a message was authorized by a domain and was not altered in transit. Multiple providers can coexist by using different DKIM selectors.
- **DMARC (Domain-based Message Authentication, Reporting, and Conformance):** a domain policy/reporting layer built on SPF and DKIM alignment. DMARC policy is a separate deployment decision from simply making inbound routing work.
- **CNAME (Canonical Name):** a DNS alias from one hostname to another. Postmark's custom Return-Path uses a CNAME.
- **Return-Path:** the envelope/bounce address used for delivery-status handling; it is distinct from the human-visible `From` address.
- **TTL (Time To Live):** how long recursive DNS resolvers may cache a record before asking again.
- **SMTP (Simple Mail Transfer Protocol):** the standard protocol used between mail systems. D'Acqua Dolce does not run a public SMTP server.
- **IMAP (Internet Message Access Protocol):** a mailbox-access protocol. D'Acqua Dolce does not need an IMAP server for the application Customer Inbox.
- **Webhook:** an HTTPS callback sent by one service to another when an event occurs; Postmark uses the inbound webhook to deliver normalized inbound message data to FastAPI.

## 2. Data model

The communication archive is separate from the transport-only `email_deliveries` ledger.

Commissioned archive tables:

- `communication_threads`
- `communication_messages`
- `communication_recipients`
- `communication_attachments`
- `communication_events`

The schema is introduced by Alembic revision:

    c41b7e2a9d63

Ownership in production:

    dacqua_dolce_migrator

Runtime CRUD role:

    dacqua_dolce_app

`email_deliveries` remains intentionally metadata-only. Do not add complete correspondence bodies to that table.

### Messages

`communication_messages` records:

- inbound/outbound/internal direction;
- delivery/archive state;
- Postmark provider and provider message identifier;
- message stream;
- RFC `Message-ID` / `In-Reply-To` linkage where available;
- sender address/name;
- subject;
- text and HTML bodies;
- redaction flag;
- sent/received timestamps.

Authentication/security messages such as password-reset or verification mail may be delivered with live tokens while the durable archive stores redacted token values. The `content_redacted` flag records that distinction.

### Recipients

`communication_recipients` normalizes:

- To
- CC
- BCC
- Reply-To

into separate rows associated with the archived message.

### Attachments

Inbound attachments are decoded from Postmark's base64 payload and stored in PostgreSQL with:

- filename;
- content type;
- content ID/disposition when supplied;
- byte length;
- SHA-256 digest;
- binary content.

The application enforces a cumulative 35 MiB inbound attachment archive limit to match the provider boundary.

### Events

Provider events are normalized into `communication_events`.

For inbound receipt, the event type is:

    inbound_received

The event record stores normalized metadata rather than a second copy of the raw email payload or attachment bodies.

## 3. Outbound archival

Existing transactional email flows archive the durable correspondence while preserving the existing Postmark transport behavior.

Examples include:

- account email verification;
- password reset;
- customer quote receipt;
- quote/operator notification;
- other callers of the central email-delivery service.

For a successful Postmark send, the archive is updated with the provider MessageID and sent state/timestamp.

For failed or suppressed sends, the durable message remains archived with the appropriate state.

Sensitive values that must be delivered to the recipient are redacted in the archive copy where required.

## 4. Inbound webhook security boundary

Public endpoint:

    POST /api/webhooks/postmark/inbound

The endpoint is machine-to-machine and is exempted only from the application's browser CSRF requirement for this exact path.

It is protected by HTTP Basic authentication. Credentials are read from protected runtime configuration:

    DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME
    DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD

The endpoint fails closed:

- missing production webhook credentials -> `503`;
- absent/incorrect Basic Auth -> `401`;
- authenticated malformed payload -> `422`;
- valid new inbound payload -> `200`;
- duplicate Postmark MessageID -> `200` with duplicate handling.

Credential comparisons use constant-time comparison.

Do not publish the username/password or a complete authenticated webhook URL in Git, documentation, screenshots, tickets, chat, or shell history.

## 5. Nginx boundary

The ordinary HTTPS server request-body limit remains:

    client_max_body_size 2m;

Only the exact inbound Postmark endpoint receives the larger envelope:

    location = /api/webhooks/postmark/inbound {
        client_max_body_size 64m;
        ...
    }

The larger envelope accommodates Postmark JSON plus base64-encoded attachments without increasing the request-body limit for the rest of the site.

The canonical source is:

    infra/production/nginx/dacqua-dolce-https.conf.template

Install the repo-managed configuration with:

    sudo scripts/production/install_nginx_site.sh \
      https \
      dacquadolce.com \
      www.dacquadolce.com

Then validate:

    sudo nginx -t
    systemctl is-active nginx

Do not hand-maintain a divergent live Nginx rule when the repository template can express the production state.

## 6. Inbound parsing and thread matching

The Postmark payload is schema-validated before archival.

Current thread resolution order:

1. `MailboxHash` containing an existing D'Acqua Dolce communication-thread UUID;
2. RFC `In-Reply-To` matching a previously archived message's internet Message-ID;
3. otherwise create a new communication thread.

When possible, an inbound sender is associated with an existing application user by normalized email address.

The inbound message stores both plain-text and HTML forms when present.

## 7. Idempotency and retry safety

`communication_messages` has a unique provider/provider-message-ID boundary.

For Postmark inbound processing, duplicate webhook delivery of the same `MessageID` returns the existing archived message instead of creating a second message.

This was validated in production with a real inbound message that Postmark retried: the provider MessageID fingerprint matched one and only one PostgreSQL `communication_messages` row.

This behavior is important because Postmark retries inbound webhooks when it does not receive a successful response.

## 8. Protected production configuration

Application configuration:

    /etc/dacqua-dolce/backend.env

Expected ownership/mode from the production hardening baseline:

    root:dacqua-app
    0640

Relevant non-secret variable names:

    DACQUA_PUBLIC_ORIGIN
    DACQUA_EMAIL_PROVIDER
    DACQUA_POSTMARK_SERVER_TOKEN
    DACQUA_EMAIL_FROM
    DACQUA_EMAIL_SUPPORT_FROM
    DACQUA_EMAIL_OPERATOR_TO
    DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME
    DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD

Never put populated secret values into the repository.

`DACQUA_EMAIL_FROM` is the transactional no-reply identity used for account
mail. `DACQUA_EMAIL_SUPPORT_FROM` is the customer-facing sender for employee
conversation replies. The thread-specific Postmark inbound alias belongs only
in the outbound `Reply-To` header and protected server configuration; the
Operations API filters Postmark inbound-routing recipient addresses so the
assigned inbound mailbox is not exposed in the employee web UI.

The observability reporting environment is separate:

    /etc/dacqua-observability/reporting.env

Do not assume application-email commissioning automatically commissions observability report delivery.

## 9. Clean Postmark + Cloudflare inbound setup order

Use this order for a new company/domain or a D'Acqua Dolce rebuild. Vendor-generated values must be taken from the current provider dashboards rather than copied blindly from an old environment.

1. Establish a business-controlled recovery/bootstrap email identity that does not depend on the custom domain. D'Acqua Dolce currently keeps a provider-native recovery identity for this purpose.
2. Establish/restore the Postmark Server under business-controlled ownership.
3. Add/verify the sending domain in Postmark and record the Postmark-generated DKIM selector/value and custom Return-Path CNAME.
4. Configure the application Postmark server token only in protected server configuration.
5. Deploy the application schema/code through the normal release mechanism so Alembic reaches `c41b7e2a9d63` or a later compatible head.
6. Generate strong inbound webhook Basic Auth credentials and store them only in `/etc/dacqua-dolce/backend.env`.
7. Restart the API and validate the webhook over loopback: wrong credentials -> `401`; correct credentials + `{}` -> `422`.
8. Install the canonical HTTPS Nginx template and repeat the authentication-boundary test through public HTTPS.
9. In Postmark, configure the **Default Inbound Stream** webhook using the authenticated HTTPS URL prepared privately in Section 10. Keep raw-email inclusion disabled unless a later requirement explicitly justifies it.
10. Use Postmark **Check** and confirm the synthetic message is archived.
11. Create the Cloudflare zone and import existing DNS **before** changing authoritative nameservers. Preserve the web origin, `www`, Postmark Return-Path, and Postmark DKIM records. Keep mail/third-party records DNS-only; D'Acqua Dolce also keeps its web records DNS-only at this checkpoint.
12. Change the registrar delegation to the provider-assigned Cloudflare nameservers only after the imported zone is complete. Keep DNSSEC disabled during the delegation migration unless an already-correct DS/DNSSEC migration has been explicitly planned.
13. Verify public resolvers and the Cloudflare authoritative nameservers return the expected web and Postmark records, and verify HTTPS still returns the expected status codes.
14. Enable Cloudflare Email Routing and allow Cloudflare to create its current MX/SPF/DKIM routing records. Do not overwrite the separate Postmark DKIM selector or Postmark Return-Path CNAME.
15. Add the private Postmark inbound address as a Cloudflare **Destination Address** and complete Cloudflare's verification message through the D'Acqua Dolce Customer Inbox. Do not record that private destination in Git/docs.
16. Create an enabled routing rule for `support@dacquadolce.com` -> the verified private Postmark destination. Leave catch-all disabled unless the business deliberately decides otherwise.
17. Send one controlled external message to `support@dacquadolce.com` and verify it appears as a new inbound Customer Inbox conversation.
18. Verify one threaded employee reply/return-reply round trip when reply routing itself has materially changed. Avoid repeating live acceptance mail for unrelated releases.

Current D'Acqua Dolce DNS/mail-routing shape:

    registrar: Moniker
    authoritative DNS: Cloudflare
    web apex A: 144.202.114.17 (DNS only)
    www: CNAME -> dacquadolce.com (DNS only)
    Postmark Return-Path: pm-bounces -> pm.mtasv.net (DNS only)
    Postmark DKIM selector: 20260917171819pm._domainkey
    Cloudflare Email Routing: root MX/SPF + Cloudflare DKIM selector
    public customer address: support@dacquadolce.com
    catch-all: disabled

The current Cloudflare Email Routing MX priorities/hostnames and DKIM/SPF values are public DNS data, but they are provider-managed implementation details. During a rebuild, prefer the values Cloudflare currently proposes rather than assuming old values can never change.

## 10. Safe credential preparation for Postmark UI

When a rebuilt system needs the authenticated webhook URL copied into the Postmark dashboard, avoid printing it.

A safe pattern is:

    sudo python3 - <<'PY'
    from pathlib import Path
    import os
    import pwd

    env_path = Path("/etc/dacqua-dolce/backend.env")
    out_path = Path("/home/n8/.postmark-inbound-webhook-url")

    wanted = {
        "DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME",
        "DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD",
    }

    values = {}

    for line in env_path.read_text().splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        if key.strip() in wanted:
            values[key.strip()] = value.strip()

    missing = sorted(key for key in wanted if not values.get(key))
    if missing:
        raise SystemExit("Missing webhook configuration: " + ", ".join(missing))

    url = (
        "https://"
        f"{values['DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME']}:"
        f"{values['DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD']}"
        "@dacquadolce.com/api/webhooks/postmark/inbound"
    )

    out_path.write_text(url)

    account = pwd.getpwnam("n8")
    os.chown(out_path, account.pw_uid, account.pw_gid)
    os.chmod(out_path, 0o600)

    print("PASS: private webhook URL prepared without displaying it")
    PY

From local macOS, copy it directly to the clipboard and remove the temporary server file:

    ssh -T dacqua-prod \
      'cat ~/.postmark-inbound-webhook-url && rm -f ~/.postmark-inbound-webhook-url' \
      | tr -d '\r\n' \
      | pbcopy

Do not run `cat` interactively on the server or otherwise display the populated URL.

## 11. Production validation

### API authentication boundary

Validate first over loopback and then through the public HTTPS endpoint:

- unauthenticated/wrong credentials -> `401`;
- authenticated `{}` -> `422`.

This proves routing/authentication without archiving a real message.

### Synthetic provider validation

Use Postmark **Check**. A successful check must produce `200` and an archived inbound message/event.

### Real inbound acceptance

For transport/webhook commissioning, one controlled message to the private Postmark inbound destination may be used before public routing exists. Once the public route is commissioned, normal acceptance should target `support@dacquadolce.com` instead of exposing or teaching operators to use the provider-assigned address.

The public-address acceptance validated on 2026-09-22 was:

    external Gmail sender
      -> support@dacquadolce.com
      -> Cloudflare Email Routing
      -> private Postmark inbound destination
      -> Postmark webhook
      -> D'Acqua Dolce Customer Inbox

Validate by metadata only. Avoid printing full message bodies, full provider IDs, attachment bytes, verification tokens, or the complete assigned inbound address.

A useful provider/database correlation technique is to compare short one-way fingerprints of Postmark MessageIDs rather than displaying the IDs themselves.

### Threaded employee reply acceptance

The production acceptance conversation contains three messages in one durable thread:

    inbound received -> outbound sent -> inbound received

This proves that an employee reply sent from Customer Inbox can be answered with the customer's normal Reply action and routed back into the same thread through the private thread-specific `Reply-To` alias.

## 12. Operational diagnostics

Nginx request status:

    sudo grep \
      'POST /api/webhooks/postmark/inbound' \
      /var/log/nginx/access.log \
      | tail -n 20

API service log:

    sudo journalctl \
      -u dacqua-dolce-api.service \
      --since "30 minutes ago" \
      --no-pager

Do not paste customer message bodies or secrets into incident records.

Useful PostgreSQL checks should prefer:

- counts;
- timestamps;
- directions/statuses;
- presence/absence of provider IDs;
- short fingerprints;
- body character counts;
- attachment counts and digests.

## 13. Privacy and retention boundary

The application now stores durable correspondence bodies and attachment bytes in PostgreSQL. That makes the communications archive materially more sensitive than the transport-only delivery ledger.

Operational requirements:

- restrict access through application RBAC and database-role boundaries;
- include the archive in database backup/restore and disaster-recovery planning;
- avoid dumping bodies/attachments into logs;
- define a business retention/deletion policy before broad employee use;
- honor future privacy/deletion requirements consistently across messages, attachments, and backups;
- keep raw Postmark webhook payload duplication disabled unless a specific requirement justifies it.

## 14. Current pending work

Commissioned:

- authenticated employee Customer Inbox list/detail UI with active/archive/all views;
- independent scrolling for the thread list and selected conversation;
- employee replies archived into the existing communication thread;
- thread-specific Postmark `Reply-To` routing using `MailboxHash`;
- production round trip proving employee outbound -> customer reply -> the same archived thread;
- Operations API filtering that keeps Postmark inbound-routing addresses out of the employee UI;
- manual refresh plus lightweight 60-second polling while the Operations page is open;
- public `support@dacquadolce.com` inbound routing through Cloudflare Email Routing;
- safe plain-text `http://`/`https://` URL linkification in Customer Inbox without rendering arbitrary inbound HTML.

Not yet commissioned:

- explicit communications retention/deletion/purge policy, including attachment and backup lifecycle;
- any privileged permanent-delete workflow;
- final customer-thread assignment workflow if the business needs assignment/ownership;
- additional Postmark delivery/bounce event ingestion if required;
- general employee custom-domain mailboxes such as `nathan@`, `jamie@`, `info@`, or `admin@`;
- observability-report delivery/timers;
- payment-provider checkout.

## 15. Vendor references

Re-verify vendor behavior during a rebuild because hosted-service behavior can change.

Postmark documentation used for the current design:

- https://postmarkapp.com/developer/user-guide/inbound/configure-an-inbound-server
- https://postmarkapp.com/developer/webhooks/inbound-webhook
- https://postmarkapp.com/support/article/1056-what-are-the-attachment-and-email-size-limits
- https://postmarkapp.com/support/article/understanding-inbound-webhook-retries-in-postmark

Cloudflare documentation used for the public-address routing layer:

- https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/
- https://developers.cloudflare.com/email-service/get-started/route-emails/
- https://developers.cloudflare.com/email-service/configuration/email-routing-addresses/

## Operations inbox lifecycle

The Operations Customer Inbox separates active work from retained history without deleting communication records.

- `communication_threads.status = open` appears in the default Inbox view.
- `communication_threads.status = closed` is presented to operators as Archived.
- Archived threads remain searchable in Archived and All views and can be restored to the active inbox.
- Archiving is a workflow/presentation action only. It does not delete messages, recipients, events, or attachment bytes.
- Permanent deletion is intentionally not exposed in the routine Operations UI. Retention or purge rules should be introduced only through an explicit documented policy.
- Failed archived communication messages are surfaced with a failure badge. The separate delivery-issues list also exposes failed `email_deliveries`, including legacy failures that may not be associated with a durable communication thread.
- Message bodies remain archived as plain text/HTML data, but the Operations UI renders the plain-text form and linkifies only explicit `http://` and `https://` URLs. Arbitrary inbound HTML is not executed/rendered as trusted markup.

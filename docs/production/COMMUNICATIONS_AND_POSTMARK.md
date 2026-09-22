# D'Acqua Dolce Communications and Postmark Production Runbook

## Purpose

This document is the technical source of truth for the commissioned D'Acqua Dolce application-email and customer-correspondence boundary.

It describes the validated final implementation only. It intentionally omits transient troubleshooting, failed commands, incorrect diagnostics, temporary test assumptions, and superseded implementation paths.

Production validation checkpoint:

- date: 2026-09-22;
- application source revision: `f5b7622126c57c0fae2fe06c343b225fec7e02af`;
- Postmark transactional sending: commissioned;
- PostgreSQL communications archive: commissioned;
- Postmark inbound webhook: commissioned;
- real Gmail -> Postmark -> D'Acqua Dolce inbound archival: validated;
- employee shared-inbox/reply UI: not yet commissioned.

## 1. Architecture

Application transactional mail:

    FastAPI
      -> durable PostgreSQL communication archive
      -> Postmark HTTPS API
      -> recipient mail system

Inbound customer/company mail:

    sender
      -> Postmark inbound processing
      -> HTTPS POST /api/webhooks/postmark/inbound
      -> Nginx
      -> FastAPI
      -> PostgreSQL communications archive

The production server does not need a general-purpose SMTP/IMAP mailbox stack for this workflow. Direct outbound TCP/25 remains blocked by the hosting provider and is not required by the Postmark HTTPS API path.

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
    DACQUA_EMAIL_OPERATOR_TO
    DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME
    DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD

Never put populated secret values into the repository.

The observability reporting environment is separate:

    /etc/dacqua-observability/reporting.env

Do not assume application-email commissioning automatically commissions observability report delivery.

## 9. Clean Postmark inbound setup order

Use this order on a rebuilt production environment.

1. Establish/restore the D'Acqua Dolce Postmark Server under business-controlled ownership.
2. Verify the production sending domain and sender identity.
3. Configure the application Postmark server token only in protected server configuration.
4. Deploy the application schema/code through the normal release mechanism so Alembic reaches `c41b7e2a9d63` or a later compatible head.
5. Generate strong inbound webhook Basic Auth credentials and store them only in `/etc/dacqua-dolce/backend.env`.
6. Restart the API and validate the webhook over loopback:
   - wrong credentials -> `401`;
   - correct credentials + `{}` -> `422`.
7. Install the canonical HTTPS Nginx template and verify the exact webhook location has the 64 MiB override while the ordinary site remains 2 MiB.
8. Repeat the authentication-boundary test through `https://dacquadolce.com`.
9. In Postmark, open the server's **Default Inbound Stream** settings.
10. Configure the webhook using the authenticated HTTPS URL prepared privately in Section 10 below. Do not type, log, or record the populated credential-bearing URL in documentation.
11. Keep raw-email inclusion disabled unless a later requirement explicitly justifies storing/processing it.
12. Save the webhook and use Postmark's **Check** action.
13. Confirm the synthetic inbound record appears in PostgreSQL with message, recipient, attachment/event data as applicable.
14. Send one controlled real inbound email to the Postmark-assigned inbound address.
15. Verify the real message appears in PostgreSQL and that repeated provider webhook attempts do not create duplicate message rows.

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

Use one controlled real inbound email. To conserve provider allowance and avoid unnecessary production data, do not repeatedly resend the same test.

Validate by metadata only. Avoid printing full message bodies, full provider IDs, attachment bytes, tokens, or the complete assigned inbound address.

A useful provider/database correlation technique is to compare short one-way fingerprints of Postmark MessageIDs rather than displaying the IDs themselves.

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

Not yet commissioned:

- employee shared-inbox list/detail UI;
- authenticated employee reply UI/API;
- final customer-thread assignment/status workflow;
- explicit communications retention/deletion policy;
- additional Postmark delivery/bounce event ingestion if required;
- observability-report delivery/timers;
- payment-provider checkout.

## 15. Vendor references

Re-verify vendor behavior during a rebuild because hosted-service behavior can change.

Postmark documentation used for the current design:

- https://postmarkapp.com/developer/user-guide/inbound/configure-an-inbound-server
- https://postmarkapp.com/developer/webhooks/inbound-webhook
- https://postmarkapp.com/support/article/1056-what-are-the-attachment-and-email-size-limits
- https://postmarkapp.com/support/article/understanding-inbound-webhook-retries-in-postmark

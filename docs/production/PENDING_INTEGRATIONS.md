# D'Acqua Dolce Pending Production Integrations

This file isolates intentionally unfinished work from the commissioned production runbook. Items remain here until they are implemented and validated on production.

## 1. AWS S3 + restic off-host disaster recovery

Current state:

- local PostgreSQL custom-format backup is commissioned;
- real weekly restore validation is commissioned;
- deployment-time pre-migration backup is commissioned;
- restic is installed/prepared;
- the restic repository password is stored securely and has an off-server copy;
- AWS credentials, bucket, IAM policy, repository initialization, retention, and off-host restore testing are not yet commissioned.

Future milestone must include:

- dedicated private backup bucket;
- dedicated least-privilege IAM identity/role;
- credentials stored only in protected server configuration or an appropriate AWS credential mechanism;
- initialized encrypted restic repository;
- automated copy/snapshot job;
- retention/lifecycle policy;
- `restic check` policy;
- off-host restore rehearsal;
- Prometheus/systemd monitoring of remote-backup freshness/failure;
- documented credential rotation and disaster-recovery procedure.

Do not describe off-host disaster recovery as complete until a restore from the remote repository has been rehearsed successfully.

## 2. Observability report delivery

Generator:

    /usr/local/sbin/dacqua-observability-report.py

Current state:

- dry-run report generation is validated;
- application Postmark transactional email is live;
- report delivery itself is not yet wired/validated;
- report timers remain disabled;
- Better Stack report heartbeats remain unsubmitted until the successful-delivery boundary is commissioned.

Desired schedule/recipients:

- daily — 09:00 `America/Los_Angeles` -> `nathan@nathanbrenton.com`;
- weekly — Saturday 11:00 `America/Los_Angeles` -> `nathan@nathanbrenton.com` and `jamie.dacqua.dolce@gmail.com`.

Future milestone must:

- keep recipients explicit in protected reporting configuration;
- submit through the approved Postmark path without exposing credentials;
- distinguish render success from delivery success;
- enable daily/weekly timers only after real delivery succeeds;
- submit the corresponding Better Stack heartbeat only after successful report delivery;
- monitor timer/job failure and report freshness.

## 3. Communications retention, purge, and attachment lifecycle

Commissioned:

- durable PostgreSQL communication threads/messages/recipients/attachments/events;
- authenticated Customer Inbox with Inbox/Archived/All views;
- archive/restore workflow with no data destruction;
- employee replies and thread-specific return routing;
- public `support@dacquadolce.com` inbound route through Cloudflare Email Routing -> Postmark -> production webhook;
- safe plain-text URL linkification in the Operations inbox.

Still pending as a business/data-governance decision:

- retention period(s) for customer correspondence;
- retention period(s) for attachment bytes;
- privileged permanent-delete/purge behavior, if any;
- how deletion requests propagate into backup retention and restore procedures;
- legal-hold/privacy-request handling;
- storage-growth thresholds that would justify moving attachment payloads out of PostgreSQL or introducing automated purge.

Do not add a routine hard-delete button merely to keep the Operations page tidy. Archive/restore is the normal workflow control. Permanent deletion should be policy-driven, auditable, and compatible with backup/privacy obligations.

## 4. Observability service systemd hardening

FastAPI systemd hardening is commissioned and validated. The observability services still require incremental hardening where compatible with each vendor unit.

Continue with measured changes rather than copying the FastAPI sandbox wholesale. Alertmanager remains an early candidate because its effective systemd security exposure was materially higher than the hardened API service.

For each service:

- record the current effective unit/drop-ins;
- apply only compatible sandbox controls;
- restart and validate the service/listener;
- verify Prometheus targets/alerts and Grafana health where relevant;
- run a non-interactive `systemd-analyze security ... --no-pager` comparison;
- document the final validated state only.

## 5. Pricing activation, checkout policy, and payment provider

The application preserves a strict third-party hosted/tokenized payment-data boundary, but authoritative production prices and a production payment processor/checkout flow are not yet commissioned.

Before enabling live checkout:

1. populate authoritative backend/database pricing rather than frontend/static prices;
2. confirm MAP/list/cart-only/private-quote/no-online-sale policy per product;
3. define tax, shipping/delivery, installation, deposit, quote-only, and inventory-reservation behavior;
4. select the payment processor;
5. integrate through the existing payment-provider boundary;
6. use sandbox/test mode first;
7. create payment sessions/intents server-side;
8. keep raw PAN/CVV/track/PIN data entirely outside D'Acqua Dolce;
9. authenticate and idempotently process provider webhooks;
10. map provider payment states to internal order states;
11. validate authorization/capture/cancel/refund/failure/retry paths;
12. perform a controlled production acceptance only after the business approves go-live.

## Commissioned items removed from this file

The following are no longer pending and belong in the commissioned production documents:

- rsync exact-revision workstation -> production staging;
- durable communications archive;
- outbound communication archival;
- authenticated Postmark inbound webhook;
- real inbound-email archival/idempotency validation;
- authenticated Operations Customer Inbox and threaded employee replies;
- active/archive/all communication-history workflow;
- public `support@dacquadolce.com` inbound routing through Cloudflare Email Routing;
- safe plain-text URL linkification in Customer Inbox.

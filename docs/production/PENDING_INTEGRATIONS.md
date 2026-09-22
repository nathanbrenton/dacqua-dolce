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

## 3. Durable customer communications archive and employee inbox

Current application email storage is intentionally metadata-only. `email_deliveries` does not store rendered message bodies or raw provider payloads.

The planned application boundary is:

    inbound customer reply
        -> Postmark inbound webhook
        -> FastAPI
        -> PostgreSQL communications archive

    employee reply
        -> authenticated Operations UI
        -> FastAPI
        -> PostgreSQL communications archive
        -> Postmark API

Future milestone should define dedicated models for communication threads/messages, participants/recipients, attachments or attachment metadata, delivery events, and assignment/status where appropriate.

Requirements:

- customer/company correspondence is durably archived in PostgreSQL;
- employees can work from the authenticated D'Acqua Dolce website;
- inbound Postmark webhook requests are authenticated/validated according to Postmark's supported mechanism;
- outbound messages are persisted transactionally with appropriate delivery state;
- access is role-controlled and audited;
- retention/privacy policy is explicit;
- do not repurpose `email_deliveries` into an unstructured body store merely to accelerate implementation.

A self-hosted general-purpose IMAP/Dovecot stack is not required by the current application design.

## 4. Observability service systemd hardening

FastAPI systemd hardening is commissioned and validated. The observability services were subsequently inspected service-by-service and still require an incremental hardening pass where compatible with each vendor unit.

Continue with measured changes rather than copying the FastAPI sandbox wholesale. Alertmanager was identified as an early candidate because its effective systemd security exposure remained materially higher than the hardened API service.

For each service:

- record the current effective unit/drop-ins;
- apply only compatible sandbox controls;
- restart and validate the service/listener;
- verify Prometheus targets/alerts and Grafana health where relevant;
- run a non-interactive `systemd-analyze security ... --no-pager` comparison;
- document the final validated state only.

## 5. Rsync-based local-to-production source staging

The immutable release mechanism itself already uses server-side `rsync` from the supplied source tree into a timestamped release. The remaining optimization is the **local workstation -> production staging** transport.

Through 2026-09-22, releases were staged reproducibly with `git archive` + SHA-256 + `scp`. This retransmits the complete compressed source snapshot even for small commits.

The next deployment transport improvement is to:

- materialize the exact intended Git revision into a clean local export;
- `rsync` that export to a persistent production staging/cache directory with deletion semantics;
- exclude `.git`, secrets, local `.env*`, virtual environments, `node_modules`, and build output;
- verify the staged revision/content;
- invoke the unchanged immutable `deploy_release.sh` against the staged tree.

Never rsync directly into `/srv/dacqua-dolce/current` or mutate a timestamped release in place.

After the first successful production deployment through this path, commit the exact reusable helper/command and promote the workflow from pending to the authoritative deployment runbook.

## 6. Payment provider / live checkout

The application preserves a strict third-party hosted/tokenized payment-data boundary, but a production payment provider and checkout flow are not commissioned.

Do not enable live checkout until the business selects the provider and validates authoritative prices, provider documentation, hosted/tokenized collection, webhook authentication, idempotency, refunds/voids/chargebacks, and the PCI responsibility split.

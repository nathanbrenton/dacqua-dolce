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

## 2. Better Stack report-delivery heartbeats

Direct observability report delivery is no longer pending.

Commissioned on 2026-10-01:

- `/usr/local/sbin/dacqua-observability-report.py` renders daily/weekly reports;
- `/usr/local/sbin/dacqua-observability-send-report` submits them through local Postfix;
- Vultr outbound TCP/25 is approved and validated;
- `mailout.dacquadolce.com` forward/PTR identity is aligned;
- SPF authorizes `144.202.114.17`;
- OpenDKIM selector `infra2026` signs direct infrastructure mail;
- a controlled daily report was received successfully;
- `dacqua-observability-daily-report.timer` is enabled/active for 09:00 `America/Los_Angeles`;
- `dacqua-observability-weekly-report.timer` is enabled/active for Saturday 11:00 `America/Los_Angeles`.

The remaining integration is the Better Stack successful-delivery heartbeat boundary.

Heartbeat acceptance must ensure:

1. heartbeat submission happens only after the report send path returns successfully;
2. a rendering failure, sendmail/Postfix failure, or other failed report run does not submit a success heartbeat;
3. heartbeat credentials/URLs remain in protected configuration rather than Git/docs;
4. daily and weekly heartbeat resources map to the corresponding report schedules;
5. one controlled successful run updates the intended heartbeat;
6. failure behavior is observable without generating duplicate report mail.

Do not route routine reports through the application Postmark allowance merely to simplify heartbeat integration.


## 3. Communications retention, purge, and attachment lifecycle

Commissioned:

- durable PostgreSQL communication threads/messages/recipients/attachments/events;
- authenticated Customer Inbox with Inbox/System/Archived/All views;
- archive/restore workflow with no data destruction;
- employee replies and thread-specific return routing;
- public `support@dacquadolce.com` inbound route through Cloudflare Email Routing -> Postmark -> production webhook;
- provider/source labeling in Customer Inbox;
- inbound/customer-supplied URLs are non-clickable while arbitrary inbound HTML remains untrusted;
- narrow advisory Postmark SpamAssassin/SPF evidence is surfaced when provider headers exist;
- website support submissions use CSRF, process-local IP limiting, and an invisible honeypot before archiving.

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

## 5. Public transactional commerce commissioning

The internal commerce foundations are implemented, but public hosted checkout remains intentionally closed. PT46 launch-phase configuration cannot bypass the underlying tax/payment/business guards.

### Automated tax

PT44 provides a provider-neutral tax domain and Stripe Tax test-mode adapter. Production still requires authoritative product classifications, registration/nexus configuration, filing/remittance ownership, production credentials/funding arrangement, and live-mode validation. Do not hard-code jurisdictional tax rules locally.

### Affinity24 / concrete gateway

Affinity24 is the selected processor direction, but the exact gateway provisioned for D'Acqua Dolce remains unknown. Obtain the actual gateway identity plus authoritative sandbox/API/hosted-payment/webhook/refund/void/idempotency documentation before implementing the concrete adapter. PT45 intentionally rejects guessed production adapters.

### Legal/customer-policy review

The application has versioned policy governance, quote snapshots, acknowledgement evidence, return/cancellation workflows, and PT53 portability. Final customer-facing Terms, Return, Cancellation, Privacy, Warranty/Support, and Shipping/Shipping-Insurance material still requires coordinated attorney review. Application structure is not a substitute for legal approval.

### Shipping insurance

The intended business direction is optional customer add-on, unchecked by default. Keep it disabled until provider, legal, claim, refund, and manufacturer responsibilities are finalized.

### Public support phone

The client intends to provide a dedicated business cell number before launch and may consider an 800 number later. Do not publish or invent a number until an authoritative number is supplied and approved for publication.

### Installer/referral program

PT50 provides an internal-only installer candidate registry. There is no customer-facing recommended-installer program, and no candidate may be represented as approved, licensed, insured, vetted, partnered, or affiliated without the required business/legal process.

## 6. Launch dependency evidence registry

PT51 is commissioned as an internal evidence/work-tracking layer for Automated Tax, Payment/Affinity24, Legal Review, Shipping Insurance, Public Support Phone, and Installer Program workstreams. Evidence status is informational only. Marking an item `Evidence Verified` does not alter `DACQUA_LAUNCH_PHASE`, `commerce_checkout_allowed`, or any tax/payment/service guard.

## 7. Policy portability/environment synchronization

PT53 provides explicit policy export/import rather than database synchronization. Production PostgreSQL remains authoritative for live approved policies. Recommended periodic non-production refresh is Production `Export all` -> trusted JSON bundle -> Local/Dev/Test preview/import. Lifecycle-preserving import is non-production-only and must remain disabled in Production.

## 8. Public support-form managed bot challenge / spam workflow

The current application source/rebuild target includes support-path abuse resistance (CSRF, an 8-per-15-minute process-local IP limiter, normalized payloads, authenticated-email enforcement for signed-in users, and an invisible honeypot). Website submissions are labeled as Website rather than Email in Customer Inbox. Confirm active release metadata during production operations rather than inferring deployment from Git alone.

Commissioned in production: Cloudflare Managed Turnstile for public Support and Quote/Inquiry with server-side Siteverify, protected site-key/secret handling, and verified live NGINX CSP. See `PT32_TURNSTILE.md` and `PT32_COMMISSIONING_AND_RECOVERY.md`.

Still optional/pending if abuse volume justifies it:

- periodic validation of forwarded-client-IP trust before relying on application IP limits;
- a dedicated staff Spam/Quarantine workflow if the business needs something beyond Archive;
- deliberate Postmark inbound spam-threshold or sender/domain blocking changes after false-positive review.

Do not interpret missing Postmark Spam/SPF headers as a clean verdict, and do not apply email-spam policy to `provider=web` website submissions.

## 9. Current launch posture

`DACQUA_LAUNCH_PHASE` defaults to `prelaunch`. `soft_launch` is a validation posture and also keeps hosted checkout closed. `public_launch` opens only the launch-phase gate; all independent commerce blockers still apply.

Do not enable public transactional commerce until the relevant external commissioning work above is complete and validated.

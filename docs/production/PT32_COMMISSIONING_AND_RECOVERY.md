# PT32 — commissioned public-form protections and communication recovery

## Status and ownership (verified 2026-10-08 UTC)

Production application revision `803f7bcfe13c40922e365f7a2f87c097b3a1a6b3` was deployed as immutable release `/srv/dacqua-dolce/releases/20261008T041740Z`, with pre-migration backup `/var/backups/dacqua-dolce/postgresql/dacqua_dolce_20261008T041804Z.dump`; no catalog changes were reported. Deployment health, HTTPS security headers, and guarded release validation passed. **The last Operations badge visual check after this release should still be confirmed separately**; do not confuse deployment success with browser acceptance. Current mutable configuration lives outside Git and must be rechecked during a rebuild.

The homepage **Talk to an Expert** form creates an `expert_inquiry` even when qualification/water-property data are present. Product pages create `product_inquiry`; system recommendations create `recommendation_inquiry`; earlier requests remain `legacy_quote_request`. Alembic revision `b32e10c7a9d4` adds `quote_requests.inquiry_context`; do not reclassify old rows or rewrite historical subjects. Operations Customer Inbox is the authoritative work queue. `DACQUA_EMAIL_OPERATOR_TO=` is intentionally empty in production; therefore the redundant operator Gmail email and its duplicate outbound communication are not created. Customer acknowledgements remain separately enabled. Support submissions create inbox records but **do not send customer auto-receipts**.

## 1. Trust boundaries and protected settings

- **Cloudflare dashboard:** Turnstile Managed widget for `dacquadolce.com`, with an app-specific public *site key* and private *secret*. Turnstile challenges are not proof that every challenged browser is malicious; page loading and auto-verification can increase analytics counts. Validate abuse resistance via server-side rejection outcomes, not dashboard totals alone.
- **Production Debian, root-managed:** `/etc/dacqua-dolce/turnstile-site-key` (root:root `0600`) contains the public site key for the release **build**. Although publicly embedded after compilation, the server-side deployment input is maintained in a protected file. `/etc/dacqua-dolce/backend.env` (root:dacqua-app `0640`) contains `DACQUA_TURNSTILE_ENABLED=true`, private `DACQUA_TURNSTILE_SECRET`, `DACQUA_TURNSTILE_EXPECTED_HOSTNAME=dacquadolce.com`, `DACQUA_QUOTE_ACK_ENABLED=true`, `DACQUA_QUOTE_ACK_MESSAGE_STREAM=website-acknowledgements`, `DACQUA_QUOTE_ACK_RECIPIENT_COOLDOWN_HOURS=24`, `DACQUA_QUOTE_ACK_GLOBAL_LIMIT_PER_HOUR=20`, `DACQUA_EMAIL_PROVIDER=postmark`, `DACQUA_EMAIL_FROM=no-reply@dacquadolce.com`, and **`DACQUA_EMAIL_OPERATOR_TO=`**. Do not print token values in logs, tickets or terminal output.
- **Postmark dashboard:** D’Acqua Dolce Production server; `dacquadolce.com` verified for DKIM and Return-Path, which authorizes `no-reply@dacquadolce.com` without a separate individual sender signature. The **Website Acknowledgements** stream ID is `website-acknowledgements` (Transactional). The **Default Transactional Stream** has ID `outbound` and carries other transactional mail; do not redirect account/recovery/order mail into the acknowledgement stream. Customer receipts were confirmed *Delivered* in the dedicated stream. Operator email suppression does not disable account, support-reply, inbound-webhook, or infrastructure email.
- **Other services:** Proton handles human/business mailbox traffic; Cloudflare Email Routing forwards selected inbound addresses; Postmark handles application transactional/inbound routing; Postfix/OpenDKIM is for local infrastructure monitoring only. Do not overwrite MX/SPF/DKIM/DMARC indiscriminately to commission one component.

## 2. Rebuild order (fresh host, not a direct deployment)

1. **Mac:** Select and verify an **exact Git SHA**; gather validated local dependencies and deployment assets. Preserve Git history and never put production `.env`, site secrets, Postmark tokens, private keys, or database dumps in the repository. `docs/production/REBUILD_RUNBOOK.md` remains the authoritative Debian provisioning sequence.
2. **Provider dashboards:** Recover Cloudflare zone/DNS, email routing, Proton business mailbox, verified Postmark sending domain and transactional streams, and the Turnstile Managed widget for the production hostname. Record stream **ID** rather than assuming its display name is the API value. Configure DKIM/Return-Path without breaking Proton MX or existing SPF.
3. **Debian host:** Rebuild least-privilege users, PostgreSQL, systemd, NGINX, certbot, and monitoring per canonical rebuild runbook. Restore protected `/etc/dacqua-dolce/backend.env`, `/etc/dacqua-dolce/migration.env` (`root:root 0600`), and `/etc/dacqua-dolce/turnstile-site-key` (`root:root 0600`) from trusted secrets custody, not Git. Restore authoritative production PostgreSQL before migrations; an explicitly empty rebuild is a separate choice. Restore TLS material or reissue only after DNS/port reachability are ready.
4. **NGINX:** Compare checked-in `infra/production/nginx/dacqua-dolce.conf.example` with **live** `/etc/nginx/sites-available/dacqua-dolce.conf`. Confirm `https://challenges.cloudflare.com` appears in live CSP `script-src`, `frame-src`, and `connect-src`. Changes to the repository template are **not** auto-installed by application release deployment. Back up live config, review changes, run `sudo nginx -t` and then `sudo systemctl reload nginx`. Avoid broad wildcard CSP permissions.
5. **Deploy:** Stage verified exact SHA using `scripts/production/stage_release_rsync.sh SHA n8@dacqua-prod` from Mac. On Debian validate `/home/n8/dacqua-dolce-deploy-source/.dacqua-release-revision` and manifest, then execute the canonical root deployment helper with the staged source. Frontend build injects public `VITE_TURNSTILE_SITE_KEY`; the API receives private secret at runtime. Pre-migration backup should complete and be verified before treating schema changes as accepted. Alembic, catalog reconciliation, atomic switch, readiness, public verifier, and release retention follow the canonical deployment script. Never rsync directly into the active release.
6. **Acceptance:** Check public and internal health, CSP, protected paths, negative-path Turnstile rejection, one legitimate Support form and one legitimate expert inquiry, Operations classification/badge, customer acknowledgement via the **dedicated** stream, and suppression evidence. Do not repeatedly submit from one address to overcome the cooldown; use a controlled distinct owned address only when needed. Preserve privacy by not pasting customer data, tokens, or message bodies.

## 3. Operational checks (Debian, read-only unless indicated)

- **Health after an explicit API restart:** `sudo systemctl is-active dacqua-dolce-api.service` confirms process state, **not readiness**. Uvicorn forks two workers and `/readiness` can briefly refuse connections, yielding public 502. A retry-based probe is preferable to an immediate single curl:

```bash
# Debian, after an approved restart. A maximum of 10 probes over ~20 seconds.
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8000/readiness >/dev/null; then
    printf 'PASS: readiness on attempt %s\n' "$attempt"
    break
  fi
  sleep 2
done
curl --max-time 10 -sS -o /dev/null -w 'Public health HTTP %{http_code}\n' https://dacquadolce.com/health
sudo journalctl --no-pager -u dacqua-dolce-api.service -n 40 -p err
```

- **Non-secret configuration:** `sudo awk -F= '/^DACQUA_(TURNSTILE_ENABLED|TURNSTILE_EXPECTED_HOSTNAME|QUOTE_ACK_ENABLED|QUOTE_ACK_MESSAGE_STREAM|QUOTE_ACK_RECIPIENT_COOLDOWN_HOURS|QUOTE_ACK_GLOBAL_LIMIT_PER_HOUR|EMAIL_OPERATOR_TO)=/ {print $1 "=" $2}' /etc/dacqua-dolce/backend.env` (never print provider tokens or secret keys).
- **Database:** `sudo -u postgres psql -d dacqua_dolce -Atc 'SELECT version_num FROM alembic_version;'` should show at least `b32e10c7a9d4` on the PT32 release lineage. Read-only delivery evidence: `sudo -u postgres psql -d dacqua_dolce -c "SELECT created_at, category, provider, status, provider_reference IS NOT NULL AS accepted_by_provider, error_summary FROM email_deliveries ORDER BY created_at DESC LIMIT 12;"` (errors may require redaction; do not publish recipient/message text).
- **Postmark dashboard:** Navigate to **Servers → D’Acqua Dolce Production → Website Acknowledgements → Activity** for `website-acknowledgements`; **Default Transactional Stream** maps to `outbound`. Interpret `sent` + provider reference as **provider accepted**; inspect Postmark's *Delivered* event to establish mailbox-server delivery. Arrival in the customer's mailbox remains a separate observation.
- **Suppression:** Category `quote_customer_receipt`, status `suppressed`, reason `recipient_cooldown` is expected for repeated requests by the same address within 24h. Suppression records often have provider `disabled` and no provider reference. `quote_operator_notification` should not be created for new inquiries while `DACQUA_EMAIL_OPERATOR_TO` is empty. Historical records remain unchanged. Global 20/hour limit is implemented but **has not been separately stress-tested in production**.

## 4. Security tests and failure recovery

Support honeypot requests intentionally return a generic success without storing a record. Missing/invalid/reused Turnstile tokens should fail validation; on provider verification failures the server fails closed. Confirm hostname and per-form action validation. Test with a deliberately **test-only** payload and ensure no unwanted Operations item is created. Siteverify failure and recipient cooldown are different layers: an accepted inquiry may produce a suppressed acknowledgement without indicating an application error.

- **No challenge visible / form rejects:** Confirm site key was injected at build time, current origin is allowed in the Cloudflare Turnstile widget, and the live NGINX CSP has correct domains. After a config-only change restart/reload only the affected service; after build-time site-key changes rebuild and deploy the frontend. Use private browsing to rule out stale JS; inspect CSP/Network messages instead of weakening token verification.
- **No customer receipt:** First check `email_deliveries` status, category, provider reference, and `error_summary` before resubmitting. `recipient_cooldown` is intentional. Inspect the matching Postmark stream, including Default Transactional Stream for historical messages sent before the dedicated stream was configured. Do not disable limits for convenience.
- **Public 502 after restart:** Wait for two application workers and confirm internal readiness. If persistent, inspect systemd logs, listener `ss -ltnp '( sport = :8000 )'`, secrets and database reachability. Separate NGINX errors from API failures; use the canonical guarded release rollback for a genuinely broken release. The additive inquiry-origin column is deliberately compatible with older code; do not automatically downgrade the production database merely to roll back application code.
- **Urgent abuse:** The code defaults protections off until secrets are commissioned, but commissioned production should stay protected. Disabling Turnstile is an **explicit break-glass security decision**, not a routine workaround. App-level rate limits include process-local buckets, so they are not distributed across API workers; Turnstile validation provides additional independent enforcement. Postmark and database operations do not guarantee exactly-once mail delivery: a provider acceptance before a database commit failure can leave uncertain evidence. The advisory transaction lock serializes acknowledgement sends and can reduce throughput; durable outbox remains future work.

## 5. Change control and rollback

For changes to live `/etc/dacqua-dolce/backend.env`, make a permissions-preserving root backup, change only approved keys with `sudo vi`, and restart the API; then verify readiness and public health. Files under `/etc/dacqua-dolce` are server-managed and must not be copied into Git. Changes to NGINX must pass `nginx -t` prior to reload. Reversion should restore the previous *configuration* separately from the application release rollback. For schema deployments retain the verified pre-migration backup, exact old/new SHAs and immutable release paths. See `DEPLOYMENT_AND_ROLLBACK.md`, `REBUILD_RUNBOOK.md`, `COMMUNICATIONS_AND_POSTMARK.md`, `PT32_ACKNOWLEDGEMENT_CONTROLS.md`, `PT32_TURNSTILE.md`, and `PT32_INQUIRY_ORIGIN.md`.


## 6. Dependency-ordered commissioning checklist (rebuild or re-provision)

This procedure supplements `REBUILD_RUNBOOK.md`; it does **not** replace the host-bootstrap, least-privilege PostgreSQL, restore, TLS, or observability chapters. Each gate must pass before progressing. For a routine code-only deployment on an already commissioned host, use `DEPLOYMENT_AND_ROLLBACK.md` instead. Do not confuse a provider-dashboard configuration change with a Git-managed application deployment.

### Gate A — Evidence and authority (operator workstation / Mac; read-only)

- Confirm the exact approved, full 40-character Git SHA (`git rev-parse HEAD`) and `git status --short` (empty for a clean baseline). Confirm the SHA exists in the trusted remote. Do **not** use the current local uncommitted checkout to deploy.
- Verify independently stored and access-controlled: the latest production PostgreSQL backup **and checksum**, backup decryption material if applicable, protected runtime/migration environment files or secret-custody equivalents, SSH/recovery-console access, DNS account, Cloudflare, Postmark, Proton, and monitoring access. A backup *file existing* is weaker evidence than a successful backup and verified restore.
- Record current DNS/MX/SPF/DKIM/DMARC and the provider identities **without** copying secrets into tickets. Preserve routing boundaries: Proton (business mail), Postmark (application transactions/inbound), local Postfix/OpenDKIM (monitoring).
- **STOP** if no verified business-state backup or no way to recover signing/encryption keys exists. Do not start a destructive host rebuild.

### Gate B — Provider-dashboard preparation (Cloudflare and Postmark websites; state-changing)

**Cloudflare Turnstile:** In the Cloudflare dashboard select the account's Turnstile area, locate/create the production widget, choose **Managed**, and allow the production hostname `dacquadolce.com`. Preserve the public **site key** and private **secret** in the appropriate password/secret custody system. If replacing a widget, note that the public key is compiled into the frontend; merely changing `backend.env` is insufficient. Do not paste the secret into `VITE_*` values or frontend source. The frontend's form-specific action and server Siteverify hostname/action checks must agree (`quote` for inquiry; inspect `backend/app/api/support.py` for the Support action). Cloudflare analytics record widget challenges, not unique malicious submissions; a browser opening the form can add counts.

**Cloudflare DNS:** Verify the current zone, A/AAAA targets, HTTPS route, Turnstile hostname, and application/webhook domain before cutover. Observe existing Proton MX, Postmark domain authentication, SPF, DKIM, DMARC and Email Routing entries. Do not replace the domain's MX or overwrite a combined SPF record to repair Turnstile; Turnstile itself requires no mail DNS change.

**Postmark:** In **Servers → D’Acqua Dolce Production**, verify the sending domain `dacquadolce.com` is DKIM and Return-Path verified under **Sender Signatures**. Domain authorization is sufficient for `no-reply@dacquadolce.com`; no standalone sender signature is necessary. Under the server's streams, verify that **Website Acknowledgements** is **Transactional** and its **stream ID** is exactly `website-acknowledgements`; display name is not a substitute. **Default Transactional Stream** has ID `outbound` and remains the account/security/order mail path. Confirm the production server token belongs to the intended Postmark server. Preserve separate inbound routing/webhook credentials and existing verified reply identities; do not publish webhook credentials.

**Gate:** the correct sending domain and separate transactional stream exist, and both API authentication credentials and Turnstile keys are safely recoverable. Do not enable customer acknowledgements before commissioning a separate stream.

### Gate C — Host, database and protected files (Debian; state-changing, privileged)

Follow `REBUILD_RUNBOOK.md` and host-bootstrap assets to establish Debian 13, service identities, firewall, NGINX, PostgreSQL, TLS and systemd. Restore authoritative production PostgreSQL data *before* allowing an application release to run Alembic. On a rebuild, verify restore ownership/permissions and consistency using the prescribed database-restore procedure rather than inventing `pg_restore` flags. Never substitute a newly seeded database for an actual business-state restore.

Protected settings are not supplied by Git. Install them from approved custody with correct ownership; for **existing** production, inspect without printing values:

```bash
# Debian — READ ONLY. Print permissions and selected NON-SECRET values only.
sudo stat -c '%U:%G %a %n' /etc/dacqua-dolce/backend.env /etc/dacqua-dolce/migration.env /etc/dacqua-dolce/turnstile-site-key
sudo awk -F= '/^DACQUA_(ENVIRONMENT|TURNSTILE_ENABLED|TURNSTILE_EXPECTED_HOSTNAME|QUOTE_ACK_ENABLED|QUOTE_ACK_MESSAGE_STREAM|QUOTE_ACK_RECIPIENT_COOLDOWN_HOURS|QUOTE_ACK_GLOBAL_LIMIT_PER_HOUR|EMAIL_OPERATOR_TO)=/ {print $1 "=" $2}' /etc/dacqua-dolce/backend.env
sudo -u postgres psql -d dacqua_dolce -Atc 'SELECT version_num FROM alembic_version;'
```

Expected files: `backend.env` `root:dacqua-app 640`; `migration.env` `root:root 600`; `turnstile-site-key` `root:root 600`. `DACQUA_EMAIL_OPERATOR_TO=` is **empty**, `DACQUA_TURNSTILE_ENABLED=true`, `DACQUA_QUOTE_ACK_ENABLED=true`, acknowledgement stream `website-acknowledgements`, cooldown `24`, hourly global quota `20`. `DACQUA_TURNSTILE_SECRET` and `DACQUA_POSTMARK_SERVER_TOKEN` must be populated but never echoed. `migration.env` must not be loaded as a runtime service environment. The database migration revision on the PT32 release lineage is `b32e10c7a9d4`; later revisions may supersede it.

**STOP** if a secret file is absent, an unauthorized party can read it, hostname/stream differs, or database restore state is unverified. A local development `.env` is **not** a suitable substitute.

### Gate D — Live NGINX CSP and TLS (Debian; review before changes)

A release builds a frontend, **not** the host's live NGINX config. Verify the actual file `/etc/nginx/sites-available/dacqua-dolce.conf`, not merely the Git template. Turnstile needs `https://challenges.cloudflare.com` in `script-src`, `frame-src` and `connect-src`; keep other CSP rules as restrictive as practicable. Confirm TLS is valid and the canonical origin redirects correctly.

```bash
# Debian — READ ONLY; shows public security headers, not secret material.
curl --max-time 10 -sSI https://dacquadolce.com/ | grep -iE '^(HTTP/|content-security-policy:|strict-transport-security:|x-content-type-options:|x-frame-options:|permissions-policy:|referrer-policy:)'
sudo nginx -t
```

If live CSP needs correction, make a **permissions-preserving root backup** of the live config, edit with `sudo vi`, review the resulting diff, run `sudo nginx -t`, and only after a successful test use `sudo systemctl reload nginx`. Do not copy the entire template over a commissioned file without examining divergent TLS and proxy settings. If the syntax check fails, restore the saved live config and retest; do not reload a failing configuration.

### Gate E — Stage exact source and deploy (Mac → Debian; state-changing)

```bash
# Mac — read-only preflight. The working tree must be clean; no secrets in Git.
cd "$HOME/Desktop/dacqua-dolce"
git status --short
git rev-parse HEAD
git rev-parse origin/main
# Mac — state-changing transport ONLY, after full SHA has been approved:
scripts/production/stage_release_rsync.sh FULL_40_CHARACTER_APPROVED_SHA n8@dacqua-prod
```

```bash
# Debian — read-only staging / availability verification:
cat /home/n8/dacqua-dolce-deploy-source/.dacqua-release-revision
ls -l /home/n8/dacqua-dolce-deploy-source/.dacqua-release-manifest.json
readlink -f /srv/dacqua-dolce/current
curl --max-time 10 -sS -o /dev/null -w 'Public HTTP %{http_code}\n' https://dacquadolce.com/health
# Debian — STATE-CHANGING deployment, only after staged SHA and backup readiness are verified:
sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source
```

The helper builds the frontend with protected build-time site-key input, runs the on-demand PostgreSQL backup helper **if available**, then Alembic and catalog reconciliation, atomically activates, retries readiness and checks public routes/headers. **CRITICAL:** its backup step can warn and continue if `/usr/local/sbin/dacqua-postgres-backup` is unavailable. For any schema deployment, check that utility **before** executing and stop if a backup cannot be obtained. Afterward, record successful backup path/checksum if produced, exact source revision, immutable active and rollback release paths, Alembic revision, and `total_changes` from catalog reconciliation. The `240K` PT32 backup size was observed; it is *not* a future expected size or a restore test.

### Gate F — Post-activation health and browser acceptance (read-only except intentional test submissions)

```bash
# Debian — read-only; allow for Uvicorn worker warmup after restart.
sudo systemctl --no-pager status dacqua-dolce-api.service
curl --max-time 10 -sS -o /dev/null -w 'Readiness HTTP %{http_code}\n' http://127.0.0.1:8000/readiness
curl --max-time 10 -sS -o /dev/null -w 'Public HTTP %{http_code}\n' https://dacquadolce.com/health
sudo journalctl --no-pager -u dacqua-dolce-api.service -n 40 -p err
```

Use the bounded retry example in section 3 for an immediate post-restart probe. If persistent public 502, check the local listener and API startup and then NGINX proxy state; do not immediately weaken Cloudflare verification. Verify non-public `/readiness`, `/api/docs`, and `/openapi.json` remain denied publicly, required security headers exist, and both Support and Quote/Inquiry include Turnstile UI.

**Controlled browser check:** after deploy, use one real browser session and a test-only, owned email address. Submit one **Talk to an Expert** request *with qualification/water-property fields*. Confirm success reference, exact `expert_inquiry` classification **and badge** in Operations; test the product/recommendation contexts separately when their UX is modified. Confirm Support still uses the appropriate source/type and has **no** automatic receipt. For a customer acknowledgement, use an address without a successful acknowledgement within the previous 24 hours; check delivery evidence and Postmark's dedicated stream. Repeated sends from the same address are intentionally `suppressed`, not a provider outage. With `DACQUA_EMAIL_OPERATOR_TO=` no `quote_operator_notification` should be generated for new inquiries. Historical subjects, mail and records are not rewritten.

**Gate:** health, security headers, browser submission, correct origin badge, Postmark delivery, and absence of redundant operator notices all pass. Stop and investigate any difference instead of claiming completion from a green deploy alone.

## 7. Troubleshooting, recovery and evidence preservation

### Customer acknowledgement decision tree

First inspect `email_deliveries` using the privacy-safe query in section 3, focusing on category `quote_customer_receipt`. A `suppressed` entry with `recipient_cooldown` means **no Postmark API call was intended**. A `sent` row with provider reference means provider *accepted* a call, not necessarily mailbox delivery. Verify the proper Postmark stream's **Activity** and per-message Delivered/Bounced event, then separately confirm recipient mailbox receipt. Before stream commissioning, some successful receipts appeared in `outbound`; that historical fact is **not** evidence that current routing is wrong. `failed` warrants checking the bounded error summary, provider stream permissions, verified sending domain, and correct server token. Never disable or reset cooldown merely to make an acceptance test pass. Do not expose email addresses or error details when publishing diagnostic output.

```sql
-- Debian PostgreSQL, READ ONLY. Inspect the past day without customer addresses.
SELECT created_at AT TIME ZONE 'America/Los_Angeles' AS created_pacific,
       category, provider, status,
       provider_reference IS NOT NULL AS provider_accepted,
       sent_at IS NOT NULL AS has_sent_timestamp,
       LEFT(COALESCE(error_summary,''), 120) AS outcome_detail
FROM email_deliveries
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC LIMIT 25;
```

### Database recovery versus application rollback

- **Application rollback:** use the exact prior immutable release and the existing guarded deployment rollback procedure; retain the additive `inquiry_context` column. Do not automatically run `alembic downgrade` to revert a frontend/validation problem.
- **Configuration rollback:** restore only the previous root-managed config from an approved backup, retaining correct ownership/mode; then restart the affected API service and wait for readiness. The Git release symlink does not restore files under `/etc/dacqua-dolce`.
- **NGINX rollback:** restore the reviewed backup of the live site config, run `sudo nginx -t`, then reload. NGINX CSP changes are not reverted by application release rollback.
- **Database disaster recovery:** follow canonical database restoration and checksum/restore-testing steps, with an explicit recovery point and downtime decision. The deployed migration can be forward-compatible with previous code, but any destructive restoration of a DB backup can lose writes after its timestamp. Never equate a successful `pg_dump` with a tested `pg_restore`.
- **Ambiguous acknowledgement transaction:** the provider API may accept an email while database commit subsequently fails. The existing advisory transaction lock enforces per-recipient and global quotas across workers but is not a durable exactly-once transactional outbox. Resolve against provider events and database records before re-issuing messages. This is a documented architectural limitation, not a reason to weaken suppression.

### Regression story: why browser acceptance is mandatory

PT32's first inquiry-classification release passed static checks and a backend suite but rejected homepage consultations containing `recommendation_context`: the route inferred `recommendation_inquiry` from qualification data, while the client correctly declared `expert_inquiry`. The correction preserved explicit request-origin type and added direct validation tests for combinations and HTTP 422 rejection. Separately, Starlette's deprecated `HTTP_422_UNPROCESSABLE_ENTITY` constant caused new rejection tests to fail under warnings-as-errors; `HTTP_422_UNPROCESSABLE_CONTENT` is required for the updated code. A final UI polish maps `originating_request.request_type` to the Operations badge without modifying historical record identities. Future regression testing must exercise the **actual route/classification behavior and a browser submission with water-property details**, not only Pydantic schema construction or an API service health check.

## 8. Change record and open limitations

Commissioned acceptance on 2026-10-08 UTC includes exact application revision `803f7bcfe13c40922e365f7a2f87c097b3a1a6b3`, release `/srv/dacqua-dolce/releases/20261008T041740Z`, backup `dacqua_dolce_20261008T041804Z.dump`, zero catalog changes, public route/security checks, separate Postmark `website-acknowledgements` Delivered event, and observed recipient cooldown suppression. The Operations badge deployment passed release verification; its **post-deploy visual acceptance was still awaiting explicit user confirmation** at the time of documentation reconciliation. The hourly global limit was not stress-tested; do not mark it separately production-tested. Network/provider assertions are point-in-time and must be reverified during a future rebuild.

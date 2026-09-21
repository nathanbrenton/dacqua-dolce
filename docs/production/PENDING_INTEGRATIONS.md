# D'Acqua Dolce Pending Production Integrations

This file isolates intentionally unfinished work from the commissioned production runbook. Items remain here
until they are implemented and validated on production.

## 1. AWS S3 + restic off-host disaster recovery

Current state:

- local PostgreSQL backup is commissioned;
- real weekly restore validation is commissioned;
- restic is installed/prepared;
- the restic repository password is stored securely and has an off-server copy;
- AWS credentials, bucket, IAM policy, repository initialization, retention, and off-host restore test are not
  yet commissioned.

Future milestone must include:

- dedicated private backup bucket;
- dedicated least-privilege IAM identity/role;
- credentials stored only in protected server configuration or an appropriate AWS credential mechanism;
- initialized encrypted restic repository;
- automated copy/snapshot job;
- retention policy;
- `restic check` policy;
- off-host restore rehearsal;
- Prometheus/systemd monitoring of remote-backup freshness/failure;
- documented credential rotation and disaster-recovery procedure.

## 2. Final outbound email architecture

Current state:

- direct outbound TCP/25 from `dacqua-platform-prod-01` is blocked by Vultr;
- local Postfix is preferred as the application/report submission interface;
- the final authenticated relay/hosted-mail architecture is not commissioned;
- Postmark remains available for application transactional email but must not be assumed to be the host's
  general mail transport;
- report timers remain disabled until real email delivery succeeds.

Future milestone must document the final, validated path only.

## 3. Observability report delivery

Generator:

    /usr/local/sbin/dacqua-observability-report.py

Dry-run generation is validated. After real mail delivery is commissioned:

- enable daily report at 09:00 `America/Los_Angeles`;
- enable weekly report Saturday at 11:00 `America/Los_Angeles`;
- submit the corresponding Better Stack heartbeat only after the successful mail-delivery boundary;
- monitor timer/job failure and report freshness.

## 4. Grafana dashboards — completed

Completed 2026-09-21. The production dashboard set is repo-managed and
provisioned from `observability/grafana/`. It includes Production Overview,
Host Resources, and Service & Backup Health dashboards. Rebuild, installation,
access, and validation procedures are documented in `GRAFANA_DASHBOARDS.md`.

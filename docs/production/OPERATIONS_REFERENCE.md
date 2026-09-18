# D'Acqua Dolce Production Operations Reference

This is the concise operator reference for the commissioned PT10 system. It is not a substitute for the full
rebuild procedure.

## SSH

From the authorized macOS workstation:

    ssh dacqua-prod

Production administrator work should use the normal non-root SSH account plus `sudo`.

## Public checks

    curl -fsS https://dacquadolce.com/health
    curl -fsSI https://www.dacquadolce.com/

Expected:

- `/health` returns HTTP 200 and `{"status":"ok"}`;
- `www` redirects to `https://dacquadolce.com/...`;
- public `/readiness`, `/api/docs`, and `/openapi.json` return 404.

## Local application checks

On `dacqua-platform-prod-01`:

    curl -fsS http://127.0.0.1:8000/readiness
    systemctl status dacqua-dolce-api.service --no-pager --full
    readlink -f /srv/dacqua-dolce/current

Expected readiness body:

    {"status":"ready"}

## Critical service summary

    systemctl --failed --no-pager

    systemctl is-active \
      nginx \
      postgresql \
      dacqua-dolce-api \
      node_exporter \
      prometheus \
      prometheus-blackbox-exporter \
      prometheus-alertmanager \
      grafana-server \
      loki \
      alloy \
      monit

## Internal listeners

    ss -ltnp

Expected public TCP listeners are only 22, 80, and 443. Expected internal listeners include 5432, 8000, 3000,
3100, 9090, 9093, 9096, 9100, 9115, and 12345 on loopback addresses.

## Nginx

Validate configuration:

    sudo nginx -t

Reload after a validated configuration change:

    sudo systemctl reload nginx

Inspect effective configuration:

    sudo nginx -T

## TLS / Certbot

    sudo certbot certificates
    systemctl list-timers --all --no-pager | grep certbot

Certificate material lives under `/etc/letsencrypt/` and private keys must never be committed or copied into
project documentation.

## PostgreSQL

Basic status:

    systemctl status postgresql --no-pager --full

Confirm loopback boundary:

    sudo -u postgres psql -Atqc "SHOW listen_addresses;"
    sudo -u postgres psql -Atqc "SHOW port;"

Database size:

    sudo -u postgres psql -Atqc \
      "SELECT pg_size_pretty(pg_database_size('dacqua_dolce'));"

## Prometheus

Readiness:

    curl -fsS http://127.0.0.1:9090/-/ready

Current alerts:

    curl -fsS http://127.0.0.1:9090/api/v1/alerts | python3 -m json.tool

Targets:

    curl -fsS http://127.0.0.1:9090/api/v1/targets | python3 -m json.tool

Validate configuration/rules before restart:

    sudo /usr/local/bin/promtool check config /etc/prometheus/prometheus.yml
    sudo /usr/local/bin/promtool check rules /etc/prometheus/rules/*.yml

## Loki / Alloy

Service state:

    systemctl status loki alloy --no-pager --full

Both services are internal-only. Alloy is the journald-to-Loki pipeline.

## Grafana

    systemctl status grafana-server --no-pager --full

Grafana listens only on `127.0.0.1:3000`. Do not expose it publicly merely for convenience. Administrative
access should use an authenticated private path such as an SSH tunnel when needed.

## Monit

    sudo monit status

Monit uses its Unix socket only; TCP/2812 is intentionally not exposed.

## Local database backup

Run a backup immediately:

    sudo -u postgres /usr/local/sbin/dacqua-postgres-backup

Inventory:

    sudo -u postgres ls -lh /var/backups/dacqua-dolce/postgresql/

Verify checksums:

    sudo -u postgres bash -c '
      cd /var/backups/dacqua-dolce/postgresql &&
      sha256sum --check ./*.sha256
    '

## Real restore validation

    sudo -u postgres /usr/local/sbin/dacqua-postgres-restore-check

The script restores the latest backup into a disposable database, validates application relations, and removes
the scratch database.

Confirm no scratch database remains:

    sudo -u postgres psql -Atqc \
      "SELECT datname FROM pg_database WHERE datname = 'dacqua_dolce_restore_verify';"

## Backup timers

    systemctl list-timers --all --no-pager | \
      grep -E 'dacqua-postgres-(backup|restore-check)'

Daily backup:

    03:15 America/Los_Angeles

Weekly restore validation:

    Sunday 04:15 America/Los_Angeles

## Local health timer

    systemctl status dacqua-dolce-healthcheck.timer --no-pager --full
    systemctl list-timers --all --no-pager | grep dacqua-dolce-healthcheck

The readiness check is intentionally local and runs every minute.

## Logs

Application:

    sudo journalctl -u dacqua-dolce-api.service --since today

Nginx:

    sudo journalctl -u nginx.service --since today

Prometheus:

    sudo journalctl -u prometheus.service --since today

Loki / Alloy:

    sudo journalctl -u loki.service -u alloy.service --since today

Backup/restore jobs:

    sudo journalctl \
      -u dacqua-postgres-backup.service \
      -u dacqua-postgres-restore-check.service \
      --since '-7 days'

## Host resources

    uptime
    free -h
    swapon --show
    df -h /
    df -ih /
    cat /proc/pressure/cpu
    cat /proc/pressure/memory
    cat /proc/pressure/io

## Firewall

    sudo nft list ruleset

The expected public inbound TCP set is 22/80/443. Do not open PostgreSQL or observability ports publicly.

## Fail2ban

    sudo fail2ban-client status
    sudo fail2ban-client status sshd

## Production secrets

Do not print secret values into tickets, chats, Git commits, or runbook output.

Current protected configuration namespaces include:

    /etc/dacqua-dolce/
    /etc/dacqua-observability/
    /etc/dacqua-backup/

The restic repository password is intentionally stored outside Git and has an additional off-server copy.

# Grafana Production Dashboards

D'Acqua Dolce production Grafana dashboards are managed from the application
repository rather than created manually in the Grafana UI.

Grafana remains an internal-only service bound to:

    127.0.0.1:3000

Do not expose Grafana directly to the public Internet.

## Repository layout

Dashboard provider:

    observability/grafana/provisioning/dashboards/dacqua-dolce.yaml

Dashboard definitions:

    observability/grafana/dashboards/production-overview.json
    observability/grafana/dashboards/host-resources.json
    observability/grafana/dashboards/service-backup-health.json

Local validator:

    scripts/production/validate_grafana_dashboards.py

Production installer:

    scripts/production/install_grafana_dashboards.sh

The provisioned dashboards use the existing Prometheus datasource UID:

    prometheus

No datasource credentials or other secrets belong in dashboard JSON.

## Dashboard set

### D'Acqua Dolce — Production Overview

UID:

    dacqua-prod-overview

Provides a high-level operational view including:

- public HTTPS availability;
- HTTPS probe latency;
- TLS certificate lifetime;
- currently firing Prometheus alerts;
- CPU utilization;
- available RAM;
- swap usage;
- root filesystem usage;
- major systemd service state;
- PostgreSQL backup and restore-validation timer state;
- backup and restore-validation last-trigger age;
- local application healthcheck age.

### D'Acqua Dolce — Host Resources

UID:

    dacqua-host-resources

Provides host-oriented telemetry including:

- CPU utilization;
- 1-, 5-, and 15-minute load averages;
- RAM;
- swap;
- CPU, memory, and I/O PSI;
- root filesystem usage;
- root inode usage;
- non-loopback network traffic;
- Prometheus, Loki, and Alloy resident memory;
- Prometheus, Loki, and Alloy process CPU usage.

### D'Acqua Dolce — Service & Backup Health

UID:

    dacqua-service-backup

Provides operational state including:

- Prometheus scrape target health;
- critical long-running systemd service state;
- local application healthcheck timer state;
- local healthcheck failure state and last-trigger age;
- readiness-related Prometheus alerts;
- PostgreSQL backup timer state and trigger age;
- PostgreSQL restore-validation timer state and trigger age;
- backup/restore-related Prometheus alerts;
- OOM kill telemetry;
- timer trigger-age history.

The PostgreSQL backup, PostgreSQL restore-check, and application healthcheck
services are oneshot units. They are normally inactive after a successful run.
Dashboard health therefore uses their timer state, last-trigger telemetry, and
failed state rather than requiring those oneshot services to remain active.

## Installation

Validate the repository definitions first:

    python3 scripts/production/validate_grafana_dashboards.py

Stage the Grafana files and installer onto the production host, then run:

    sudo ./scripts/production/install_grafana_dashboards.sh /path/to/staged/repository

The installer:

1. validates all three source dashboard definitions;
2. confirms the existing Prometheus datasource UID;
3. backs up any previous D'Acqua Dolce Grafana provisioning;
4. installs the provider and dashboard JSON;
5. restarts Grafana so the provider is loaded;
6. verifies Grafana health;
7. verifies Grafana remains bound only to 127.0.0.1:3000;
8. checks Grafana 13 unified storage for all three expected dashboard UIDs;
9. automatically restores the previous managed dashboard provisioning if
   Grafana fails health or provisioning validation.

Grafana 13 stores current dashboard resources through unified storage. The
legacy `dashboard` SQL table is deprecated and must not be used as the
authoritative provisioning validation source. The installer therefore checks
the `resource` table for `dashboard.grafana.app` / `dashboards` resources.

Installer backups are retained beneath:

    /var/backups/dacqua-dolce/grafana/

## Production paths

Provider:

    /etc/grafana/provisioning/dashboards/dacqua-dolce.yaml

Dashboard JSON:

    /var/lib/grafana/dashboards/dacqua-dolce/

The provider is configured with:

    allowUiUpdates: false

Changes should therefore be made in the repository and redeployed rather than
treated as mutable Grafana UI state.

## Access

Grafana should remain private.

For administrative access from an authorized workstation, use an SSH tunnel
rather than opening TCP/3000 in nftables:

    ssh -L 3000:127.0.0.1:3000 dacqua-prod

Then access Grafana locally through:

    http://127.0.0.1:3000

Authentication remains governed by the production Grafana configuration.

## Logs

Loki remains provisioned as a Grafana datasource and Grafana Explore remains
the supported log exploration interface.

A dedicated Loki dashboard is intentionally not part of this milestone because
dashboard queries should not assume Alloy/Loki labels that have not been
explicitly verified for that purpose.

## Validation

Local repository validation:

    python3 scripts/production/validate_grafana_dashboards.py

Production service health:

    systemctl status grafana-server --no-pager --full
    curl -fsS http://127.0.0.1:3000/api/health
    ss -lntp | grep '127.0.0.1:3000'

Provisioned files:

    sudo ls -l /etc/grafana/provisioning/dashboards/dacqua-dolce.yaml
    sudo ls -l /var/lib/grafana/dashboards/dacqua-dolce/

Grafana journal:

    sudo journalctl -u grafana-server --since today --no-pager

The expected dashboard UIDs are:

    dacqua-prod-overview
    dacqua-host-resources
    dacqua-service-backup

## Validated production state — 2026-09-21

Milestone 3 was validated on `dacqua-platform-prod-01` with Grafana 13.2.2.

Validated results:

- all three dashboard JSON definitions provisioned successfully;
- all three expected dashboard UIDs were present in Grafana unified storage;
- all 47 dashboard PromQL expressions executed successfully;
- public HTTPS probes returned telemetry for both canonical and www endpoints;
- Grafana health reported `database: ok`;
- Grafana remained bound to `127.0.0.1:3000`;
- there were no firing or pending Prometheus alerts;
- there were zero failed systemd units;
- the recent Grafana warning/error journal query returned no entries.

The production dashboard set is therefore considered commissioned.

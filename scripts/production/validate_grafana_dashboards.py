#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PROVIDER = (
    ROOT
    / "observability"
    / "grafana"
    / "provisioning"
    / "dashboards"
    / "dacqua-dolce.yaml"
)

DASHBOARD_DIR = ROOT / "observability" / "grafana" / "dashboards"

EXPECTED = {
    "production-overview.json": {
        "uid": "dacqua-prod-overview",
        "title": "D'Acqua Dolce — Production Overview",
    },
    "host-resources.json": {
        "uid": "dacqua-host-resources",
        "title": "D'Acqua Dolce — Host Resources",
    },
    "service-backup-health.json": {
        "uid": "dacqua-service-backup",
        "title": "D'Acqua Dolce — Service & Backup Health",
    },
}

REQUIRED_PROMQL_SNIPPETS = (
    'probe_success{job="blackbox_https"',
    "quantile_over_time(0.95, probe_duration_seconds",
    "probe_ssl_earliest_cert_expiry",
    'ALERTS{alertstate="firing"}',
    'node_cpu_seconds_total{job="node",mode="idle"}',
    'node_memory_MemAvailable_bytes{job="node"}',
    'node_memory_SwapTotal_bytes{job="node"}',
    'node_filesystem_avail_bytes{job="node",mountpoint="/"}',
    "node_systemd_unit_state",
    "dacqua-postgres-backup.timer",
    "dacqua-postgres-restore-check.timer",
    "dacqua-dolce-healthcheck.timer",
    'node_load1{job="node"}',
    'node_load5{job="node"}',
    'node_load15{job="node"}',
    "node_pressure_cpu_waiting_seconds_total",
    "node_pressure_memory_waiting_seconds_total",
    "node_pressure_memory_stalled_seconds_total",
    "node_pressure_io_waiting_seconds_total",
    "node_pressure_io_stalled_seconds_total",
    "node_filesystem_files_free",
    "node_network_receive_bytes_total",
    "node_network_transmit_bytes_total",
    'process_resident_memory_bytes{job=~"prometheus|loki|alloy"}',
    'process_cpu_seconds_total{job=~"prometheus|loki|alloy"}',
    'up{job=~"node|prometheus|blackbox_https|loki|alloy"}',
    "dacqua-dolce-healthcheck.service",
    "LocalHealthCheckOverdue|LocalHealthCheckFailed",
    "PostgreSQLBackupTimerInactive|PostgreSQLBackupOverdue",
    "PostgreSQLRestoreCheckTimerInactive|PostgreSQLRestoreCheckOverdue",
    'increase(node_vmstat_oom_kill{job="node"}[$__range])',
    'node_vmstat_oom_kill{job="node"}',
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def passed(message: str) -> None:
    print(f"PASS: {message}")


if not PROVIDER.is_file():
    fail(f"missing provider: {PROVIDER.relative_to(ROOT)}")

provider_text = PROVIDER.read_text(encoding="utf-8")

provider_requirements = (
    "apiVersion: 1",
    "folderUid: dacqua-prod",
    "type: file",
    "disableDeletion: true",
    "allowUiUpdates: false",
    "path: /var/lib/grafana/dashboards/dacqua-dolce",
)

for marker in provider_requirements:
    if marker not in provider_text:
        fail(f"provider missing marker: {marker}")

passed("Grafana provider structure")

all_expressions: list[str] = []
seen_dashboard_uids: set[str] = set()

for filename, expected in EXPECTED.items():
    path = DASHBOARD_DIR / filename

    if not path.is_file():
        fail(f"missing dashboard: {path.relative_to(ROOT)}")

    try:
        dashboard = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{filename}: invalid JSON: {exc}")

    if dashboard.get("id") is not None:
        fail(f"{filename}: provisioned dashboard id must be null")

    if dashboard.get("uid") != expected["uid"]:
        fail(
            f"{filename}: UID {dashboard.get('uid')!r} "
            f"!= {expected['uid']!r}"
        )

    if dashboard.get("title") != expected["title"]:
        fail(f"{filename}: unexpected title")

    if dashboard["uid"] in seen_dashboard_uids:
        fail(f"{filename}: duplicate dashboard UID")

    seen_dashboard_uids.add(dashboard["uid"])

    panels = dashboard.get("panels")
    if not isinstance(panels, list) or not panels:
        fail(f"{filename}: no panels")

    panel_ids: set[int] = set()

    for panel in panels:
        panel_id = panel.get("id")

        if not isinstance(panel_id, int):
            fail(f"{filename}: panel without integer id")

        if panel_id in panel_ids:
            fail(f"{filename}: duplicate panel id {panel_id}")

        panel_ids.add(panel_id)

        targets = panel.get("targets", [])

        for target in targets:
            datasource = target.get("datasource", {})

            if datasource.get("uid") != "prometheus":
                fail(
                    f"{filename}: panel {panel_id} target does not "
                    "use datasource UID 'prometheus'"
                )

            expr = target.get("expr")
            if not isinstance(expr, str) or not expr.strip():
                fail(f"{filename}: panel {panel_id} has empty PromQL")

            all_expressions.append(expr)

    encoded = json.dumps(dashboard).lower()

    forbidden = (
        '"password"',
        '"token"',
        '"api_key"',
        '"heartbeat"',
        "${ds_prometheus}",
    )

    for marker in forbidden:
        if marker in encoded:
            fail(f"{filename}: forbidden marker {marker!r}")

    passed(
        f"{filename}: JSON, UID, panels, datasource references"
    )

joined_expressions = "\n".join(all_expressions)

for snippet in REQUIRED_PROMQL_SNIPPETS:
    if snippet not in joined_expressions:
        fail(f"required PromQL marker missing: {snippet}")

passed("All three dashboards have expected telemetry coverage")
passed("No dashboard secrets or datasource variables")
passed("Task 3.1 + 3.2 + 3.3 Grafana provisioning package")

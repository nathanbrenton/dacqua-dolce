#!/usr/bin/env bash

set -u
umask 022

SOURCE_ROOT="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"

PROVIDER_SRC="$SOURCE_ROOT/observability/grafana/provisioning/dashboards/dacqua-dolce.yaml"
DASHBOARD_SRC_DIR="$SOURCE_ROOT/observability/grafana/dashboards"

PROVIDER_DST="/etc/grafana/provisioning/dashboards/dacqua-dolce.yaml"
DASHBOARD_DST_DIR="/var/lib/grafana/dashboards/dacqua-dolce"

BACKUP_BASE="/var/backups/dacqua-dolce/grafana"

DASHBOARDS=(
  "production-overview.json"
  "host-resources.json"
  "service-backup-health.json"
)

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

rollback() {
    printf '\nROLLBACK: restoring previous Grafana dashboard provisioning\n'

    if [ "$provider_existed" -eq 1 ]; then
        cp -a "$backup_dir/dacqua-dolce.yaml" "$PROVIDER_DST"
    else
        rm -f "$PROVIDER_DST"
    fi

    rm -rf "$DASHBOARD_DST_DIR"

    if [ "$dashboard_dir_existed" -eq 1 ]; then
        cp -a "$backup_dir/dacqua-dolce-dashboard-dir" "$DASHBOARD_DST_DIR"
    fi

    systemctl restart grafana-server >/dev/null 2>&1 || true

    printf 'ROLLBACK: previous Grafana provisioning restored\n'
}

if [ "$(id -u)" -ne 0 ]; then
    die "run this installer with sudo"
fi

[ -f "$PROVIDER_SRC" ] ||
    die "missing provider source: $PROVIDER_SRC"

for dashboard in "${DASHBOARDS[@]}"; do
    [ -f "$DASHBOARD_SRC_DIR/$dashboard" ] ||
        die "missing dashboard source: $DASHBOARD_SRC_DIR/$dashboard"
done

getent group grafana >/dev/null ||
    die "grafana group does not exist"

systemctl cat grafana-server >/dev/null 2>&1 ||
    die "grafana-server systemd unit is unavailable"

grep -RqsE '^[[:space:]]*uid:[[:space:]]*prometheus[[:space:]]*$' \
    /etc/grafana/provisioning/datasources ||
    die "provisioned Prometheus datasource UID 'prometheus' was not found"

printf '\n===== SOURCE VALIDATION =====\n'

python3 - "$DASHBOARD_SRC_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])

expected = {
    "production-overview.json": (
        "dacqua-prod-overview",
        "D'Acqua Dolce — Production Overview",
    ),
    "host-resources.json": (
        "dacqua-host-resources",
        "D'Acqua Dolce — Host Resources",
    ),
    "service-backup-health.json": (
        "dacqua-service-backup",
        "D'Acqua Dolce — Service & Backup Health",
    ),
}

seen = set()

for filename, (uid, title) in expected.items():
    path = root / filename

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"FAIL: {filename}: {exc}")

    if data.get("uid") != uid:
        raise SystemExit(
            f"FAIL: {filename}: unexpected UID {data.get('uid')!r}"
        )

    if data.get("title") != title:
        raise SystemExit(
            f"FAIL: {filename}: unexpected title {data.get('title')!r}"
        )

    if data.get("id") is not None:
        raise SystemExit(
            f"FAIL: {filename}: provisioned dashboard id must be null"
        )

    if uid in seen:
        raise SystemExit(f"FAIL: duplicate dashboard UID: {uid}")

    seen.add(uid)

    print(f"PASS: {filename}: {uid}")

print("PASS: source dashboards validated")
PY

if [ "$?" -ne 0 ]; then
    die "source dashboard validation failed"
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$BACKUP_BASE/$timestamp"

mkdir -p "$backup_dir" ||
    die "could not create backup directory: $backup_dir"

provider_existed=0
dashboard_dir_existed=0

if [ -f "$PROVIDER_DST" ]; then
    provider_existed=1
    cp -a "$PROVIDER_DST" "$backup_dir/dacqua-dolce.yaml" ||
        die "could not back up existing provider"
fi

if [ -d "$DASHBOARD_DST_DIR" ]; then
    dashboard_dir_existed=1
    cp -a "$DASHBOARD_DST_DIR" \
        "$backup_dir/dacqua-dolce-dashboard-dir" ||
        die "could not back up existing dashboard directory"
fi

printf '\n===== INSTALL =====\n'

install -d \
    -o root \
    -g grafana \
    -m 0755 \
    /etc/grafana/provisioning/dashboards ||
    die "could not prepare Grafana provisioning directory"

install -d \
    -o root \
    -g grafana \
    -m 0755 \
    "$DASHBOARD_DST_DIR" ||
    die "could not prepare dashboard directory"

install \
    -o root \
    -g grafana \
    -m 0644 \
    "$PROVIDER_SRC" \
    "$PROVIDER_DST" ||
    die "could not install provider"

for dashboard in "${DASHBOARDS[@]}"; do
    install \
        -o root \
        -g grafana \
        -m 0644 \
        "$DASHBOARD_SRC_DIR/$dashboard" \
        "$DASHBOARD_DST_DIR/$dashboard" ||
        die "could not install $dashboard"

    printf 'INSTALLED: %s\n' "$dashboard"
done

printf 'BACKUP: %s\n' "$backup_dir"

printf '\n===== RESTART GRAFANA =====\n'

if ! systemctl restart grafana-server; then
    rollback
    die "grafana-server restart failed"
fi

healthy=0

for attempt in $(seq 1 15); do
    if curl -fsS \
        http://127.0.0.1:3000/api/health \
        >/dev/null 2>&1
    then
        healthy=1
        break
    fi

    sleep 2
done

if [ "$healthy" -ne 1 ]; then
    journalctl \
        -u grafana-server \
        -n 50 \
        --no-pager \
        --full >&2

    rollback
    die "Grafana did not become healthy after provisioning"
fi

printf 'PASS: Grafana health endpoint\n'

printf '\n===== BINDING CHECK =====\n'

if ! ss -lnt |
    awk '$4 == "127.0.0.1:3000" { found=1 } END { exit !found }'
then
    rollback
    die "Grafana is not listening on expected 127.0.0.1:3000"
fi

if ss -lnt |
    awk '$4 == "0.0.0.0:3000" || $4 == "[::]:3000" { found=1 } END { exit !found }'
then
    rollback
    die "Grafana unexpectedly has a public/wildcard port 3000 listener"
fi

printf 'PASS: Grafana remains loopback-only on 127.0.0.1:3000\n'

printf '\n===== PROVISIONED DASHBOARD UNIFIED-STORAGE CHECK =====\n'

python3 - <<'PYINNER'
import sqlite3
import time

db = "/var/lib/grafana/grafana.db"

expected = {
    "dacqua-prod-overview",
    "dacqua-host-resources",
    "dacqua-service-backup",
}

deadline = time.monotonic() + 30
last_found = set()

while time.monotonic() < deadline:
    con = sqlite3.connect(
        f"file:{db}?mode=ro",
        uri=True,
        timeout=5,
    )

    try:
        columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info(resource)"
            ).fetchall()
        }

        required_columns = {
            "group",
            "resource",
            "namespace",
            "name",
        }

        missing_columns = required_columns - columns

        if missing_columns:
            raise SystemExit(
                "FAIL: Grafana unified-storage resource table "
                f"is missing columns: {sorted(missing_columns)}"
            )

        placeholders = ",".join("?" for _ in expected)

        rows = con.execute(
            f"""
            SELECT name
            FROM resource
            WHERE "group" = ?
              AND resource = ?
              AND namespace = ?
              AND name IN ({placeholders})
            ORDER BY name
            """,
            (
                "dashboard.grafana.app",
                "dashboards",
                "default",
                *sorted(expected),
            ),
        ).fetchall()
    finally:
        con.close()

    last_found = {row[0] for row in rows}

    if last_found == expected:
        for uid in sorted(last_found):
            print(f"PASS: unified storage contains {uid}")

        print(
            "PASS: all three dashboards loaded into "
            "Grafana unified storage"
        )
        raise SystemExit(0)

    time.sleep(2)

print(
    "FAIL: Grafana unified storage did not contain "
    "all expected dashboards"
)
print("found:", sorted(last_found))
print("missing:", sorted(expected - last_found))
raise SystemExit(1)
PYINNER

if [ "$?" -ne 0 ]; then
    journalctl \
        -u grafana-server \
        -n 80 \
        --no-pager \
        --full >&2

    rollback
    die "Grafana did not provision all expected dashboard UIDs"
fi

printf '\n===== INSTALLED FILES =====\n'
ls -l \
    "$PROVIDER_DST" \
    "$DASHBOARD_DST_DIR"/*.json

printf '\nPASS: D'\''Acqua Dolce Grafana dashboards installed and validated\n'

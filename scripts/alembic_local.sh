#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA="$ROOT/infra"
BACKEND="$ROOT/backend"

if [[ ! -f "$INFRA/.env" || ! -f "$BACKEND/.env" ]]; then
  echo "ERROR: expected infra/.env and backend/.env" >&2
  exit 2
fi

read_env_key() {
  python3 - "$INFRA/.env" "$1" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
wanted = sys.argv[2]

for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    if key.strip() == wanted:
        print(value.strip().strip('"').strip("'"))
        raise SystemExit(0)

raise SystemExit(1)
PY
}

POSTGRES_DB="$(read_env_key POSTGRES_DB)" || {
  echo "ERROR: POSTGRES_DB is required in infra/.env" >&2
  exit 2
}
POSTGRES_USER="$(read_env_key POSTGRES_USER)" || {
  echo "ERROR: POSTGRES_USER is required in infra/.env" >&2
  exit 2
}
MIGRATOR_PASSWORD="$(read_env_key DACQUA_DB_MIGRATOR_PASSWORD)" || {
  echo "ERROR: DACQUA_DB_MIGRATOR_PASSWORD is required in infra/.env" >&2
  exit 2
}

if [[ "$POSTGRES_DB" != "dacqua_dolce_dev" || "$POSTGRES_USER" != "dacqua_dolce_dba" ]]; then
  echo "ERROR: refusing local Alembic wrapper outside dacqua_dolce_dev / dacqua_dolce_dba" >&2
  exit 2
fi

if [[ ! -x "$BACKEND/.venv/bin/alembic" ]]; then
  echo "ERROR: expected backend/.venv/bin/alembic" >&2
  exit 2
fi

encoded_password="$(
  DACQUA_RAW_PASSWORD="$MIGRATOR_PASSWORD" python3 -c \
    'import os, urllib.parse; print(urllib.parse.quote(os.environ["DACQUA_RAW_PASSWORD"], safe=""))'
)"

export DACQUA_MIGRATION_DATABASE_URL="postgresql+psycopg://dacqua_dolce_migrator:${encoded_password}@127.0.0.1:15432/dacqua_dolce_dev"

cd "$BACKEND"
exec .venv/bin/alembic "$@"

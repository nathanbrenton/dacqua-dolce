#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/rebuild_local_database.sh --confirm-destroy-local-data

Destructively rebuilds ONLY the local D'Acqua Dolce development PostgreSQL
volume after validating the expected local database/bootstrap identities.

Before destroying the volume, the script creates a pg_dump backup when an
existing local PostgreSQL container is available.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" != "--confirm-destroy-local-data" ]]; then
  usage >&2
  echo >&2
  echo "ERROR: destructive local rebuild requires --confirm-destroy-local-data" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA="$ROOT/infra"
BACKUP_DIR="$ROOT/.local-backups"

if [[ ! -f "$INFRA/.env" ]]; then
  echo "ERROR: $INFRA/.env is required" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1091
source "$INFRA/.env"
set +a

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
: "${DACQUA_DB_APP_PASSWORD:?DACQUA_DB_APP_PASSWORD is required}"
: "${DACQUA_DB_MIGRATOR_PASSWORD:?DACQUA_DB_MIGRATOR_PASSWORD is required}"

if [[ "$POSTGRES_DB" != "dacqua_dolce_dev" || "$POSTGRES_USER" != "dacqua_dolce_dba" ]]; then
  echo "ERROR: refusing destructive rebuild: expected local dacqua_dolce_dev / dacqua_dolce_dba" >&2
  exit 2
fi

mkdir -p "$BACKUP_DIR"

if docker inspect dacqua-dolce-postgres >/dev/null 2>&1; then
  old_user="$(docker exec dacqua-dolce-postgres printenv POSTGRES_USER)"
  old_db="$(docker exec dacqua-dolce-postgres printenv POSTGRES_DB)"
  stamp="$(date +%Y%m%dT%H%M%S)"
  backup="$BACKUP_DIR/dacqua-dolce-dev-before-uam-$stamp.dump"
  echo "Backing up existing local database to: $backup"
  docker exec dacqua-dolce-postgres pg_dump -Fc -U "$old_user" -d "$old_db" > "$backup"
  test -s "$backup"
else
  echo "No existing local PostgreSQL container found; no pre-reset dump was possible."
fi

cd "$INFRA"
docker compose down -v
docker compose up -d postgres

for _ in {1..30}; do
  if docker compose exec -T postgres pg_isready -U dacqua_dolce_dba -d dacqua_dolce_dev >/dev/null 2>&1; then
    echo "Local PostgreSQL rebuild completed."
    exit 0
  fi
  sleep 1
done

echo "ERROR: local PostgreSQL did not become ready" >&2
exit 1

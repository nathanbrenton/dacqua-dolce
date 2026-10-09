#!/usr/bin/env bash
# PT35: isolated, disposable local PostgreSQL backend regression runner.
set -u

fail() { printf 'PT35 REFUSED: %s\n' "$*" >&2; exit 1; }
info() { printf 'PT35: %s\n' "$*"; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)" || fail 'cannot resolve repository root'
CLUSTER="$HOME/Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17"
LOG="$HOME/Desktop/dacqua-dolce_build-assets/test-infrastructure/pt35-postgres17.log"
PORT=55433
ADMIN=pt35_admin
HOST=127.0.0.1
PREFIX=dacqua_pt35_run_

[[ "$(uname -s)" == Darwin ]] || fail 'macOS-only runner'
[[ -d "$CLUSTER" && ! -L "$CLUSTER" ]] || fail 'dedicated PT35 cluster missing or symlinked; initialize it manually first'
[[ -f "$CLUSTER/PG_VERSION" ]] || fail 'cluster marker missing'
[[ "$(cat "$CLUSTER/PG_VERSION")" == 17 ]] || fail 'cluster must be PostgreSQL 17'
[[ -f "$ROOT/backend/.venv/bin/python" && -f "$ROOT/backend/.venv/bin/alembic" ]] || fail 'backend virtual environment missing'
for cmd in pg_ctl psql createdb dropdb pg_isready; do command -v "$cmd" >/dev/null 2>&1 || fail "missing $cmd"; done

# Never point PostgreSQL or libpq at inherited external configuration.
unset PGDATABASE PGSERVICE PGSERVICEFILE PGHOST PGHOSTADDR PGPORT PGUSER PGOPTIONS PGDATA PGPASSFILE PGPASSWORD
export PGCONNECT_TIMEOUT=3

started_here=0
created_db=0
DB=''
cleanup() {
  code=$?
  trap - EXIT INT TERM
  if [[ $created_db == 1 && -n "$DB" ]]; then
    info "removing disposable database $DB"
    if ! dropdb --if-exists --force -h "$HOST" -p "$PORT" -U "$ADMIN" -- "$DB"; then
      info 'WARNING: disposable database cleanup failed; manual inspection required'
      code=1
    fi
  fi
  if [[ $started_here == 1 ]]; then
    info 'stopping PT35 cluster started by this runner'
    if ! pg_ctl -D "$CLUSTER" stop -m fast; then
      info 'WARNING: PT35 cluster shutdown failed'
      code=1
    fi
  fi
  if [[ $code == 0 ]]; then info 'regression completed successfully'; else info "regression failed (exit $code)"; fi
  exit "$code"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Refuse if a PostgreSQL process on the dedicated port is not OUR cluster.
if pg_ctl -D "$CLUSTER" status >/dev/null 2>&1; then
  info 'PT35 cluster is already running; verifying its identity'
else
  if pg_isready -h "$HOST" -p "$PORT" >/dev/null 2>&1; then
    fail "port $PORT already responds while PT35 cluster is stopped"
  fi
  info 'starting PT35 cluster'
  pg_ctl -D "$CLUSTER" -l "$LOG" start || fail 'PT35 cluster startup failed'
  started_here=1
fi

identity="$(psql -h "$HOST" -p "$PORT" -U "$ADMIN" -d postgres -X -A -t -v ON_ERROR_STOP=1 -c "SELECT current_user || '|' || current_database() || '|' || inet_server_port() || '|' || current_setting('data_directory')" 2>/dev/null)" || fail 'cannot verify dedicated cluster identity'
expected="${ADMIN}|postgres|${PORT}|${CLUSTER}"
[[ "$identity" == "$expected" ]] || fail 'PostgreSQL identity/data directory mismatch'

# Explicitly leave the original dacqua_pt35_test database untouched.
DB="${PREFIX}$(date -u +%Y%m%d%H%M%S)_$$"
[[ "$DB" =~ ^dacqua_pt35_run_[0-9]{14}_[0-9]+$ ]] || fail 'invalid disposable database identifier'
info "creating disposable database $DB"
createdb -h "$HOST" -p "$PORT" -U "$ADMIN" -O "$ADMIN" -- "$DB" || fail 'database creation failed'
created_db=1

url="postgresql+psycopg://${ADMIN}@${HOST}:${PORT}/${DB}"
export DACQUA_ENVIRONMENT=test
export DACQUA_DATABASE_URL="$url"
export DACQUA_MIGRATION_DATABASE_URL="$url"
export DACQUA_SESSION_COOKIE_SECURE=false
# Generate a fresh test-only key; never echo it, persist it, or read .env.
DACQUA_MFA_ENCRYPTION_KEY="$("$ROOT/backend/.venv/bin/python" -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" || fail 'unable to generate test MFA key'
export DACQUA_MFA_ENCRYPTION_KEY

info 'applying Alembic migrations to disposable database'
(cd "$ROOT/backend" && .venv/bin/alembic upgrade head) || fail 'Alembic migrations failed'

check="$(psql -h "$HOST" -p "$PORT" -U "$ADMIN" -d "$DB" -X -A -t -v ON_ERROR_STOP=1 -c "SELECT current_user || '|' || current_database() || '|' || inet_server_port()" 2>/dev/null)" || fail 'unable to verify migrated test database'
[[ "$check" == "${ADMIN}|${DB}|${PORT}" ]] || fail 'test database identity mismatch'

info 'running full backend pytest suite'
(cd "$ROOT" && backend/.venv/bin/python -m pytest backend -q --tb=short "$@")
result=$?
exit "$result"

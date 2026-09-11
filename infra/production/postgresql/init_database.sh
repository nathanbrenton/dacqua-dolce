#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

APP_PASSWORD="${DACQUA_DB_APP_PASSWORD:-}"

if [ -z "${APP_PASSWORD}" ]; then
  echo "ERROR: DACQUA_DB_APP_PASSWORD must be supplied in the environment"
  exit 1
fi

if printf '%s' "${APP_PASSWORD}" | grep -q $'[\n\r]'; then
  echo "ERROR: database password contains a newline"
  exit 1
fi

ROLE_EXISTS="$(
  sudo -u postgres \
    psql \
    -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname = 'dacqua_dolce_app'"
)"

if [ "${ROLE_EXISTS}" != "1" ]; then
  sudo -u postgres \
    psql \
    --set=ON_ERROR_STOP=1 \
    --set=app_password="${APP_PASSWORD}" \
    <<'SQL'
CREATE ROLE dacqua_dolce_app
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    PASSWORD :'app_password';
SQL
else
  echo "Role dacqua_dolce_app already exists."
fi

DB_EXISTS="$(
  sudo -u postgres \
    psql \
    -tAc \
    "SELECT 1 FROM pg_database WHERE datname = 'dacqua_dolce'"
)"

if [ "${DB_EXISTS}" != "1" ]; then
  sudo -u postgres \
    createdb \
    --owner=dacqua_dolce_app \
    --encoding=UTF8 \
    dacqua_dolce
else
  echo "Database dacqua_dolce already exists."
fi

sudo -u postgres \
  psql \
  --set=ON_ERROR_STOP=1 \
  --dbname=dacqua_dolce \
  <<'SQL'
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO dacqua_dolce_app;
SQL

echo "Database and application role ready."

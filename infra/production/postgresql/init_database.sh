#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

APP_PASSWORD="${DACQUA_DB_APP_PASSWORD:-}"
MIGRATOR_PASSWORD="${DACQUA_DB_MIGRATOR_PASSWORD:-}"

if [ -z "${APP_PASSWORD}" ]; then
  echo "ERROR: DACQUA_DB_APP_PASSWORD must be supplied in the environment"
  exit 1
fi

if [ -z "${MIGRATOR_PASSWORD}" ]; then
  echo "ERROR: DACQUA_DB_MIGRATOR_PASSWORD must be supplied in the environment"
  exit 1
fi

if printf '%s' "${APP_PASSWORD}" | grep -q $'[\n\r]'; then
  echo "ERROR: application database password contains a newline"
  exit 1
fi

if printf '%s' "${MIGRATOR_PASSWORD}" | grep -q $'[\n\r]'; then
  echo "ERROR: migration database password contains a newline"
  exit 1
fi

APP_ROLE_EXISTS="$(
  sudo -u postgres \
    psql \
    -X \
    -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname = 'dacqua_dolce_app'"
)"

if [ "${APP_ROLE_EXISTS}" != "1" ]; then
  sudo -u postgres \
    psql \
    -X \
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
    NOBYPASSRLS
    PASSWORD :'app_password';
SQL
else
  sudo -u postgres \
    psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --set=app_password="${APP_PASSWORD}" \
    <<'SQL'
ALTER ROLE dacqua_dolce_app
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS
    PASSWORD :'app_password';
SQL
fi

MIGRATOR_ROLE_EXISTS="$(
  sudo -u postgres \
    psql \
    -X \
    -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname = 'dacqua_dolce_migrator'"
)"

if [ "${MIGRATOR_ROLE_EXISTS}" != "1" ]; then
  sudo -u postgres \
    psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --set=migrator_password="${MIGRATOR_PASSWORD}" \
    <<'SQL'
CREATE ROLE dacqua_dolce_migrator
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS
    PASSWORD :'migrator_password';
SQL
else
  sudo -u postgres \
    psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --set=migrator_password="${MIGRATOR_PASSWORD}" \
    <<'SQL'
ALTER ROLE dacqua_dolce_migrator
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS
    PASSWORD :'migrator_password';
SQL
fi

DB_EXISTS="$(
  sudo -u postgres \
    psql \
    -X \
    -tAc \
    "SELECT 1 FROM pg_database WHERE datname = 'dacqua_dolce'"
)"

if [ "${DB_EXISTS}" != "1" ]; then
  sudo -u postgres \
    createdb \
    --owner=dacqua_dolce_migrator \
    --encoding=UTF8 \
    dacqua_dolce
else
  # The migration identity, not the runtime web identity, owns the database.
  sudo -u postgres \
    psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname=postgres \
    -c \
    "ALTER DATABASE dacqua_dolce OWNER TO dacqua_dolce_migrator"
fi

sudo -u postgres \
  psql \
  -X \
  --set=ON_ERROR_STOP=1 \
  --dbname=dacqua_dolce \
  <<'SQL'
BEGIN;

-- Transfer objects created under the original single-role deployment model.
-- On a new database this is harmless because there are no such objects yet.
REASSIGN OWNED BY dacqua_dolce_app TO dacqua_dolce_migrator;

-- The application can connect and use existing objects, but it cannot create
-- or own schema objects.
GRANT CONNECT ON DATABASE dacqua_dolce TO dacqua_dolce_app;
GRANT CONNECT ON DATABASE dacqua_dolce TO dacqua_dolce_migrator;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM dacqua_dolce_app;

GRANT USAGE ON SCHEMA public TO dacqua_dolce_app;
GRANT USAGE, CREATE ON SCHEMA public TO dacqua_dolce_migrator;

-- Normalize the runtime role to application DML only.
REVOKE ALL PRIVILEGES
    ON ALL TABLES IN SCHEMA public
    FROM dacqua_dolce_app;

GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public
    TO dacqua_dolce_app;

REVOKE ALL PRIVILEGES
    ON ALL SEQUENCES IN SCHEMA public
    FROM dacqua_dolce_app;

GRANT USAGE, SELECT, UPDATE
    ON ALL SEQUENCES IN SCHEMA public
    TO dacqua_dolce_app;

-- Future Alembic-created objects must automatically receive the same runtime
-- permissions so deployments do not require manual GRANT statements.
ALTER DEFAULT PRIVILEGES
    FOR ROLE dacqua_dolce_migrator
    IN SCHEMA public
    REVOKE ALL PRIVILEGES ON TABLES
    FROM dacqua_dolce_app;

ALTER DEFAULT PRIVILEGES
    FOR ROLE dacqua_dolce_migrator
    IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES
    TO dacqua_dolce_app;

ALTER DEFAULT PRIVILEGES
    FOR ROLE dacqua_dolce_migrator
    IN SCHEMA public
    REVOKE ALL PRIVILEGES ON SEQUENCES
    FROM dacqua_dolce_app;

ALTER DEFAULT PRIVILEGES
    FOR ROLE dacqua_dolce_migrator
    IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES
    TO dacqua_dolce_app;

COMMIT;
SQL

echo "Database, migrator role, and runtime application role ready."

#!/usr/bin/env bash
set -euo pipefail

APP_PASSWORD="${DACQUA_DB_APP_PASSWORD:?DACQUA_DB_APP_PASSWORD is required}"
MIGRATOR_PASSWORD="${DACQUA_DB_MIGRATOR_PASSWORD:?DACQUA_DB_MIGRATOR_PASSWORD is required}"
DB_NAME="${POSTGRES_DB:-dacqua_dolce_dev}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
  --set=app_password="$APP_PASSWORD" --set=migrator_password="$MIGRATOR_PASSWORD" <<'SQL'
CREATE ROLE dacqua_dolce_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD :'migrator_password';
CREATE ROLE dacqua_dolce_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD :'app_password';
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
  --set=db_name="$DB_NAME" <<'SQL'
SELECT format('ALTER DATABASE %I OWNER TO dacqua_dolce_migrator', :'db_name') \gexec
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" \
  --set=db_name="$DB_NAME" <<'SQL'
BEGIN;
SELECT format('GRANT CONNECT ON DATABASE %I TO dacqua_dolce_app', :'db_name') \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO dacqua_dolce_migrator', :'db_name') \gexec
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM dacqua_dolce_app;
GRANT USAGE ON SCHEMA public TO dacqua_dolce_app;
GRANT USAGE, CREATE ON SCHEMA public TO dacqua_dolce_migrator;
ALTER DEFAULT PRIVILEGES FOR ROLE dacqua_dolce_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dacqua_dolce_app;
ALTER DEFAULT PRIVILEGES FOR ROLE dacqua_dolce_migrator IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO dacqua_dolce_app;
COMMIT;
SQL

#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run with sudo or as root"
  exit 1
fi

APP_ROOT="/srv/dacqua-dolce"
RELEASES="${APP_ROOT}/releases"
SHARED="${APP_ROOT}/shared"
CURRENT="${APP_ROOT}/current"
ENV_FILE="/etc/dacqua-dolce/backend.env"
MIGRATION_ENV_FILE="/etc/dacqua-dolce/migration.env"
READINESS_URL="http://127.0.0.1:8000/readiness"
READINESS_ATTEMPTS=30
READINESS_DELAY_SECONDS=1
RELEASE_RETENTION_COUNT="${DACQUA_RELEASE_RETENTION_COUNT:-5}"
SOURCE_ROOT="${1:-}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

wait_for_readiness() {
  local attempt

  for attempt in $(seq 1 "${READINESS_ATTEMPTS}"); do
    if curl \
      --fail \
      --silent \
      --show-error \
      --max-time 5 \
      "${READINESS_URL}" >/dev/null 2>&1; then
      return 0
    fi

    sleep "${READINESS_DELAY_SECONDS}"
  done

  return 1
}

atomic_switch() {
  local target="$1"

  rm -f "${CURRENT}.new"
  ln -s "${target}" "${CURRENT}.new"
  mv -Tf "${CURRENT}.new" "${CURRENT}"
}

validate_release_path() {
  local path="$1"

  case "${path}" in
    "${RELEASES}"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T[0-9][0-9][0-9][0-9][0-9][0-9]Z)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

normalize_release_permissions() {
  local release="$1"

  chown -R root:root "${release}"
  chmod -R go-w "${release}"
}

verify_public_release() {
  local release="$1"
  local verifier="${release}/scripts/production/verify_release.sh"

  if [ ! -x "${verifier}" ]; then
    echo "WARNING: public release verifier not present in release; local readiness is the activation gate"
    return 0
  fi

  "${verifier}" "${DACQUA_PUBLIC_ORIGIN}"
}

rollback_after_failed_activation() {
  local failed_release="$1"
  local previous_release="$2"

  echo "ERROR: post-switch validation failed for ${failed_release}" >&2

  if [ -z "${previous_release}" ] \
    || [ ! -d "${previous_release}" ] \
    || ! validate_release_path "${previous_release}"; then
    echo "ERROR: no valid previous release is available for automatic rollback" >&2
    return 1
  fi

  echo "Attempting automatic application rollback to: ${previous_release}"
  atomic_switch "${previous_release}"
  systemctl restart dacqua-dolce-api.service

  if ! wait_for_readiness; then
    echo "CRITICAL: previous release did not recover readiness after rollback" >&2
    return 1
  fi

  echo "PASS: previous release recovered readiness"
  rm -rf "${failed_release}"
  echo "Removed failed release: ${failed_release}"
  return 0
}

prune_old_releases() {
  local current_real
  local index=0
  local release_path
  local release_name
  local -a releases=()

  current_real="$(readlink -f "${CURRENT}")"

  mapfile -t releases < <(
    find "${RELEASES}" \
      -mindepth 1 \
      -maxdepth 1 \
      -type d \
      -printf '%f\n' \
    | grep -E '^[0-9]{8}T[0-9]{6}Z$' \
    | sort -r
  )

  for release_name in "${releases[@]}"; do
    index=$((index + 1))

    if [ "${index}" -le "${RELEASE_RETENTION_COUNT}" ]; then
      continue
    fi

    release_path="${RELEASES}/${release_name}"

    if [ "${release_path}" = "${current_real}" ]; then
      echo "WARNING: refusing to prune current release: ${release_path}"
      continue
    fi

    echo "Pruning old release: ${release_path}"
    rm -rf "${release_path}"
  done
}

if [ -z "${SOURCE_ROOT}" ]; then
  echo "usage: $0 /path/to/release-source"
  exit 2
fi

SOURCE_ROOT="$(cd "${SOURCE_ROOT}" && pwd -P)"

if [ ! -d "${SOURCE_ROOT}/backend" ] \
  || [ ! -d "${SOURCE_ROOT}/frontend" ]; then
  fail "release source must contain backend/ and frontend/"
fi

if [ ! -r "${ENV_FILE}" ]; then
  fail "production environment file is missing: ${ENV_FILE}"
fi

if [ ! -r "${MIGRATION_ENV_FILE}" ]; then
  fail "migration environment file is missing: ${MIGRATION_ENV_FILE}"
fi

if ! [[ "${RELEASE_RETENTION_COUNT}" =~ ^[0-9]+$ ]] \
  || [ "${RELEASE_RETENTION_COUNT}" -lt 2 ]; then
  fail "DACQUA_RELEASE_RETENTION_COUNT must be an integer >= 2"
fi

set -a
# shellcheck disable=SC1090
. "${ENV_FILE}"
# shellcheck disable=SC1090
. "${MIGRATION_ENV_FILE}"
set +a

: "${DACQUA_DATABASE_URL:?DACQUA_DATABASE_URL is required}"
: "${DACQUA_MIGRATION_DATABASE_URL:?DACQUA_MIGRATION_DATABASE_URL is required}"
: "${DACQUA_MFA_ENCRYPTION_KEY:?DACQUA_MFA_ENCRYPTION_KEY is required}"
: "${DACQUA_PUBLIC_ORIGIN:?DACQUA_PUBLIC_ORIGIN is required}"

for required_value in \
  "${DACQUA_DATABASE_URL}" \
  "${DACQUA_MFA_ENCRYPTION_KEY}" \
  "${DACQUA_PUBLIC_ORIGIN}"
do
  if printf '%s' "${required_value}" | grep -q 'REPLACE_'; then
    fail "required production environment value still contains a REPLACE_* placeholder"
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RELEASE="${RELEASES}/${STAMP}"
PREVIOUS_RELEASE=""
ACTIVATED=0

if [ -L "${CURRENT}" ]; then
  PREVIOUS_RELEASE="$(readlink -f "${CURRENT}")"

  if ! validate_release_path "${PREVIOUS_RELEASE}"; then
    fail "current symlink does not resolve to a valid release: ${PREVIOUS_RELEASE}"
  fi
fi

cleanup_unactivated_release() {
  local status=$?

  if [ "${status}" -ne 0 ] \
    && [ "${ACTIVATED}" -eq 0 ] \
    && [ -d "${RELEASE}" ]; then
    echo "Cleaning incomplete release: ${RELEASE}" >&2
    rm -rf "${RELEASE}"
  fi
}

trap cleanup_unactivated_release EXIT

install -d -o root -g root -m 0755 \
  "${APP_ROOT}" \
  "${RELEASES}" \
  "${RELEASE}"

install -d -o root -g dacqua-app -m 0750 \
  "${SHARED}"

echo "Creating release: ${RELEASE}"

rsync -a \
  --delete \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude 'node_modules/' \
  --exclude '.venv/' \
  "${SOURCE_ROOT}/" \
  "${RELEASE}/"

cd "${RELEASE}/backend"
python3 -m venv .venv

PIP_SOURCE_ARGS=()

if [ -n "${DACQUA_PYTHON_WHEELHOUSE:-}" ]; then
  if [ ! -d "${DACQUA_PYTHON_WHEELHOUSE}" ]; then
    fail "DACQUA_PYTHON_WHEELHOUSE is not a directory"
  fi

  PIP_SOURCE_ARGS+=(
    --no-index
    --find-links "${DACQUA_PYTHON_WHEELHOUSE}"
  )
fi

./.venv/bin/python -m pip install \
  --no-input \
  "${PIP_SOURCE_ARGS[@]}" \
  -c constraints-known-good.txt \
  .

cd "${RELEASE}/frontend"
npm ci
npm run build

if [ -x /usr/local/sbin/dacqua-postgres-backup ]; then
  echo "Creating pre-migration PostgreSQL backup"
  sudo -u postgres /usr/local/sbin/dacqua-postgres-backup
else
  echo "WARNING: /usr/local/sbin/dacqua-postgres-backup is unavailable; proceeding without an on-demand pre-migration backup"
fi

cd "${RELEASE}/backend"
./.venv/bin/alembic upgrade head

echo "Reconciling canonical production catalog"
./.venv/bin/python -m app.cli.seed_catalog apply

# The deploy-only database credential is no longer needed after migrations
# and deployment-time catalog reconciliation.
unset DACQUA_MIGRATION_DATABASE_URL

normalize_release_permissions "${RELEASE}"

printf 'Release owner after normalization: '
stat -c '%U:%G %a %n' "${RELEASE}"

atomic_switch "${RELEASE}"
ACTIVATED=1

systemctl daemon-reload
systemctl restart dacqua-dolce-api.service

if ! wait_for_readiness; then
  if rollback_after_failed_activation "${RELEASE}" "${PREVIOUS_RELEASE}"; then
    fail "deployment failed readiness validation; previous release was restored"
  fi

  fail "deployment failed readiness validation and automatic rollback did not recover production"
fi

echo "PASS: local readiness"

if ! verify_public_release "${RELEASE}"; then
  if rollback_after_failed_activation "${RELEASE}" "${PREVIOUS_RELEASE}"; then
    fail "deployment failed public validation; previous release was restored"
  fi

  fail "deployment failed public validation and automatic rollback did not recover production"
fi

echo "PASS: post-switch production validation"

prune_old_releases

trap - EXIT

echo
echo "Release active: ${RELEASE}"

if [ -n "${PREVIOUS_RELEASE}" ]; then
  echo "Previous release retained for rollback: ${PREVIOUS_RELEASE}"
fi

echo "Release retention count: ${RELEASE_RETENTION_COUNT}"

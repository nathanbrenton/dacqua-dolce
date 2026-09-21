#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run with sudo or as root"
  exit 1
fi

APP_ROOT="/srv/dacqua-dolce"
RELEASES="${APP_ROOT}/releases"
CURRENT="${APP_ROOT}/current"
ENV_FILE="/etc/dacqua-dolce/backend.env"
READINESS_URL="http://127.0.0.1:8000/readiness"
READINESS_ATTEMPTS=30
READINESS_DELAY_SECONDS=1
TARGET="${1:-}"

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

validate_release_name() {
  local name="$1"
  [[ "${name}" =~ ^[0-9]{8}T[0-9]{6}Z$ ]]
}

verify_public_release() {
  local release="$1"
  local verifier="${release}/scripts/production/verify_release.sh"

  if [ ! -x "${verifier}" ]; then
    echo "WARNING: public release verifier not present in target release; local readiness is the rollback gate"
    return 0
  fi

  "${verifier}" "${DACQUA_PUBLIC_ORIGIN}"
}

if [ -z "${TARGET}" ]; then
  echo "Current release:"
  readlink -f "${CURRENT}" 2>/dev/null || true

  echo
  echo "Available releases:"
  find "${RELEASES}" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -printf '%f\n' \
    | grep -E '^[0-9]{8}T[0-9]{6}Z$' \
    | sort -r

  echo
  echo "usage: $0 RELEASE_DIRECTORY_NAME"
  exit 2
fi

if ! validate_release_name "${TARGET}"; then
  fail "release name must match YYYYMMDDTHHMMSSZ"
fi

RELEASE="${RELEASES}/${TARGET}"

if [ ! -d "${RELEASE}" ]; then
  fail "release not found: ${RELEASE}"
fi

if [ ! -L "${CURRENT}" ]; then
  fail "current release symlink is missing: ${CURRENT}"
fi

ORIGINAL_RELEASE="$(readlink -f "${CURRENT}")"

if [ "${ORIGINAL_RELEASE}" = "${RELEASE}" ]; then
  echo "Release is already active: ${RELEASE}"
  exit 0
fi

if [ ! -r "${ENV_FILE}" ]; then
  fail "production environment file is missing: ${ENV_FILE}"
fi

set -a
# shellcheck disable=SC1090
. "${ENV_FILE}"
set +a

: "${DACQUA_PUBLIC_ORIGIN:?DACQUA_PUBLIC_ORIGIN is required}"

echo "Application rollback target: ${RELEASE}"
echo "Database schema will NOT be downgraded."
echo "Original release: ${ORIGINAL_RELEASE}"

atomic_switch "${RELEASE}"
systemctl restart dacqua-dolce-api.service

if wait_for_readiness && verify_public_release "${RELEASE}"; then
  echo
  echo "PASS: rollback release is healthy"
  echo "Rolled back to: ${RELEASE}"
  exit 0
fi

echo "ERROR: rollback target failed validation; restoring original release" >&2
atomic_switch "${ORIGINAL_RELEASE}"
systemctl restart dacqua-dolce-api.service

if wait_for_readiness; then
  echo "PASS: original release recovered readiness" >&2
  fail "requested rollback was rejected because the target did not validate"
fi

fail "rollback target failed and original release did not recover readiness"

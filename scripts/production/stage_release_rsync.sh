#!/usr/bin/env bash
set -euo pipefail

REVISION="${1:-HEAD}"
SSH_TARGET="${2:-${DACQUA_PROD_SSH_TARGET:-dacqua-prod}}"
REMOTE_STAGE_NAME="${DACQUA_PROD_STAGE_DIR_NAME:-dacqua-dolce-deploy-source}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

case "${REMOTE_STAGE_NAME}" in
  *[!A-Za-z0-9._-]*)
    fail "DACQUA_PROD_STAGE_DIR_NAME may contain only letters, numbers, dot, underscore, and hyphen"
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [ -z "${REPO_ROOT}" ]; then
  fail "run this helper from inside the D'Acqua Dolce Git repository"
fi

if [ ! -f "${REPO_ROOT}/scripts/production/deploy_release.sh" ] \
  || [ ! -f "${REPO_ROOT}/scripts/production/verify_staged_source.py" ]; then
  fail "repository does not contain the production deployment helpers"
fi

FULL_REV="$(git -C "${REPO_ROOT}" rev-parse --verify "${REVISION}^{commit}")"

if ! [[ "${FULL_REV}" =~ ^[0-9a-f]{40}$ ]]; then
  fail "resolved revision is not a 40-character Git commit ID"
fi

if [ -n "$(git -C "${REPO_ROOT}" status --short)" ]; then
  echo "NOTE: working tree has uncommitted changes; they are NOT included in this staged release."
fi

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dacqua-release.XXXXXX")"
EXPORT_ROOT="${TEMP_ROOT}/source"

cleanup() {
  rm -rf "${TEMP_ROOT}"
}
trap cleanup EXIT

mkdir -p "${EXPORT_ROOT}"

echo "===== EXACT REVISION EXPORT ====="
echo "Repository: ${REPO_ROOT}"
echo "Revision:   ${FULL_REV}"

git -C "${REPO_ROOT}" archive --format=tar "${FULL_REV}" \
  | tar -xf - -C "${EXPORT_ROOT}"

python3 "${EXPORT_ROOT}/scripts/production/verify_staged_source.py" \
  write \
  "${EXPORT_ROOT}" \
  "${FULL_REV}"

REMOTE_HOME="$(ssh "${SSH_TARGET}" 'printf "%s" "$HOME"')"

case "${REMOTE_HOME}" in
  /*)
    ;;
  *)
    fail "could not resolve an absolute remote home directory for ${SSH_TARGET}"
    ;;
esac

REMOTE_STAGE="${REMOTE_HOME}/${REMOTE_STAGE_NAME}"

ssh "${SSH_TARGET}" "mkdir -p '${REMOTE_STAGE}'"

echo
echo "===== RSYNC SOURCE STAGE ====="
echo "Target: ${SSH_TARGET}:${REMOTE_STAGE}/"

rsync \
  -acz \
  --delete \
  --itemize-changes \
  --stats \
  "${EXPORT_ROOT}/" \
  "${SSH_TARGET}:${REMOTE_STAGE}/"

echo
echo "===== REMOTE STAGE VERIFICATION ====="

ssh "${SSH_TARGET}" \
  "python3 '${REMOTE_STAGE}/scripts/production/verify_staged_source.py' verify '${REMOTE_STAGE}' '${FULL_REV}'"

echo
echo "PASS: exact revision staged successfully"
echo "Revision: ${FULL_REV}"
echo "Stage:    ${REMOTE_STAGE}"
echo
echo "Deployment command:"
echo "  sudo '${REMOTE_STAGE}/scripts/production/deploy_release.sh' '${REMOTE_STAGE}'"

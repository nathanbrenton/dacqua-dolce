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

SOURCE_ROOT="${1:-}"

if [ -z "${SOURCE_ROOT}" ]; then
  echo "usage: $0 /path/to/release-source"
  exit 2
fi

if [ ! -d "${SOURCE_ROOT}/backend" ] \
  || [ ! -d "${SOURCE_ROOT}/frontend" ]; then
  echo "ERROR: release source must contain backend/ and frontend/"
  exit 1
fi

if [ ! -r "${ENV_FILE}" ]; then
  echo "ERROR: production environment file is missing: ${ENV_FILE}"
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "${ENV_FILE}"
set +a

: "${DACQUA_DATABASE_URL:?DACQUA_DATABASE_URL is required}"
: "${DACQUA_MFA_ENCRYPTION_KEY:?DACQUA_MFA_ENCRYPTION_KEY is required}"
: "${DACQUA_PUBLIC_ORIGIN:?DACQUA_PUBLIC_ORIGIN is required}"

for required_value in \
  "${DACQUA_DATABASE_URL}" \
  "${DACQUA_MFA_ENCRYPTION_KEY}" \
  "${DACQUA_PUBLIC_ORIGIN}"
do
  if printf '%s' "${required_value}" | grep -q 'REPLACE_'; then
    echo "ERROR: required production environment value still contains a REPLACE_* placeholder"
    exit 1
  fi
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RELEASE="${RELEASES}/${STAMP}"

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
    echo "ERROR: DACQUA_PYTHON_WHEELHOUSE is not a directory"
    exit 1
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

./.venv/bin/alembic upgrade head

cd "${RELEASE}/frontend"

npm ci
npm run build

ln -sfn "${RELEASE}" "${CURRENT}.new"
mv -Tf "${CURRENT}.new" "${CURRENT}"

systemctl daemon-reload
systemctl restart dacqua-dolce-api.service

sleep 2

curl \
  --fail \
  --silent \
  --show-error \
  --max-time 10 \
  http://127.0.0.1:8000/readiness

echo
echo "Release active: ${RELEASE}"

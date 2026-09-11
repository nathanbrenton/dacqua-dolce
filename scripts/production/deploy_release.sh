#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/srv/dacqua-dolce"
RELEASES="${APP_ROOT}/releases"
SHARED="${APP_ROOT}/shared"
CURRENT="${APP_ROOT}/current"

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

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RELEASE="${RELEASES}/${STAMP}"

mkdir -p \
  "${RELEASES}" \
  "${SHARED}" \
  "${RELEASE}"

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

#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/srv/dacqua-dolce"
RELEASES="${APP_ROOT}/releases"
CURRENT="${APP_ROOT}/current"

TARGET="${1:-}"

if [ -z "${TARGET}" ]; then
  echo "Available releases:"
  find "${RELEASES}" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    -printf '%f\n' \
    | sort -r

  echo
  echo "usage: $0 RELEASE_DIRECTORY_NAME"
  exit 2
fi

RELEASE="${RELEASES}/${TARGET}"

if [ ! -d "${RELEASE}" ]; then
  echo "ERROR: release not found: ${RELEASE}"
  exit 1
fi

ln -sfn "${RELEASE}" "${CURRENT}.new"
mv -Tf "${CURRENT}.new" "${CURRENT}"

systemctl restart dacqua-dolce-api.service

sleep 2

curl \
  --fail \
  --silent \
  --show-error \
  --max-time 10 \
  http://127.0.0.1:8000/readiness

echo
echo "Rolled back to: ${RELEASE}"

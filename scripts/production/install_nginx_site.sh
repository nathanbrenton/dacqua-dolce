#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

MODE="${1:-}"
SERVER_NAME="${2:-}"

if [ "${MODE}" != "http" ]   && [ "${MODE}" != "https" ]; then
  echo "usage: $0 http|https SERVER_NAME"
  exit 2
fi

if ! printf '%s' "${SERVER_NAME}"   | grep -Eq '^[A-Za-z0-9.-]+$'; then
  echo "ERROR: invalid server name"
  exit 1
fi

SCRIPT_DIR="$(
  CDPATH= cd -- "$(dirname -- "$0")"     && pwd
)"

REPO_ROOT="$(
  CDPATH= cd -- "${SCRIPT_DIR}/../.."     && pwd
)"

TEMPLATE="${REPO_ROOT}/infra/production/nginx/dacqua-dolce-${MODE}.conf.template"

if [ ! -f "${TEMPLATE}" ]; then
  echo "ERROR: Nginx template not found:"
  echo "       ${TEMPLATE}"
  exit 1
fi

if [ "${MODE}" = "https" ]; then
  CERT_ROOT="/etc/letsencrypt/live/${SERVER_NAME}"

  if [ ! -s "${CERT_ROOT}/fullchain.pem" ]     || [ ! -s "${CERT_ROOT}/privkey.pem" ]; then
    echo "ERROR: TLS certificate files are missing."
    echo "Issue the certificate before enabling HTTPS."
    exit 1
  fi
fi

TMP="$(mktemp)"
trap 'rm -f "${TMP}"' EXIT

sed   "s/__SERVER_NAME__/${SERVER_NAME}/g"   "${TEMPLATE}"   > "${TMP}"

install   -o root   -g root   -m 0644   "${TMP}"   /etc/nginx/sites-available/dacqua-dolce.conf

ln -sfn   /etc/nginx/sites-available/dacqua-dolce.conf   /etc/nginx/sites-enabled/dacqua-dolce.conf

rm -f   /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

echo
echo "PASS: Nginx ${MODE} site enabled for ${SERVER_NAME}"

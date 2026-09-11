#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

ADMIN_USER="${1:-}"
PUBLIC_KEY_FILE="${2:-}"

if [ -z "${ADMIN_USER}" ] || [ -z "${PUBLIC_KEY_FILE}" ]; then
  echo "usage: $0 ADMIN_USER /path/to/public-key.pub"
  exit 2
fi

if [ ! -s "${PUBLIC_KEY_FILE}" ]; then
  echo "ERROR: public key file missing or empty"
  exit 1
fi

if ! id "${ADMIN_USER}" >/dev/null 2>&1; then
  adduser \
    --disabled-password \
    --gecos "" \
    "${ADMIN_USER}"
fi

usermod -aG sudo "${ADMIN_USER}"

HOME_DIR="$(getent passwd "${ADMIN_USER}" | cut -d: -f6)"

install -d \
  -o "${ADMIN_USER}" \
  -g "${ADMIN_USER}" \
  -m 0700 \
  "${HOME_DIR}/.ssh"

install \
  -o "${ADMIN_USER}" \
  -g "${ADMIN_USER}" \
  -m 0600 \
  "${PUBLIC_KEY_FILE}" \
  "${HOME_DIR}/.ssh/authorized_keys"

echo "Admin user ready: ${ADMIN_USER}"
echo "Verify SSH key login before running SSH hardening."

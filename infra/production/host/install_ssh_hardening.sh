#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

ADMIN_USER="${1:-}"
SOURCE="${2:-}"

if [ -z "${ADMIN_USER}" ] || [ -z "${SOURCE}" ]; then
  echo "usage: $0 ADMIN_USER /path/to/sshd-dacqua-hardening.conf"
  exit 2
fi

if ! id "${ADMIN_USER}" >/dev/null 2>&1; then
  echo "ERROR: admin user does not exist: ${ADMIN_USER}"
  exit 1
fi

HOME_DIR="$(getent passwd "${ADMIN_USER}" | cut -d: -f6)"
AUTHORIZED_KEYS="${HOME_DIR}/.ssh/authorized_keys"

if [ ! -s "${AUTHORIZED_KEYS}" ]; then
  echo "ERROR: refusing SSH lockdown."
  echo "No non-empty authorized_keys file found for ${ADMIN_USER}."
  exit 1
fi

if [ ! -f "${SOURCE}" ]; then
  echo "ERROR: SSH hardening source not found: ${SOURCE}"
  exit 1
fi

install \
  -o root \
  -g root \
  -m 0644 \
  "${SOURCE}" \
  /etc/ssh/sshd_config.d/60-dacqua-hardening.conf

sshd -t

systemctl reload ssh

echo
echo "SSH hardening installed and sshd syntax validated."
echo "KEEP THE CURRENT SSH SESSION OPEN."
echo "Open a second terminal and confirm key-only login before disconnecting."

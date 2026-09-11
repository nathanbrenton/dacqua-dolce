#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

SOURCE="${1:-}"

if [ -z "${SOURCE}" ] || [ ! -f "${SOURCE}" ]; then
  echo "usage: $0 /path/to/fail2ban-dacqua.local"
  exit 2
fi

install \
  -o root \
  -g root \
  -m 0644 \
  "${SOURCE}" \
  /etc/fail2ban/jail.d/dacqua.local

fail2ban-client -t

systemctl enable fail2ban
systemctl restart fail2ban

fail2ban-client status sshd

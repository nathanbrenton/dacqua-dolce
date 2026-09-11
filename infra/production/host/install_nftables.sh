#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

SOURCE="${1:-}"

if [ -z "${SOURCE}" ] || [ ! -f "${SOURCE}" ]; then
  echo "usage: $0 /path/to/nftables.conf"
  exit 2
fi

nft -c -f "${SOURCE}"

install \
  -o root \
  -g root \
  -m 0644 \
  "${SOURCE}" \
  /etc/nftables.conf

systemctl enable nftables
systemctl restart nftables

echo "Active nftables rules:"
nft list ruleset

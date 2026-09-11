#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run this script as root"
  exit 1
fi

if [ ! -r /etc/os-release ]; then
  echo "ERROR: /etc/os-release not found"
  exit 1
fi

. /etc/os-release

if [ "${ID:-}" != "debian" ]; then
  echo "ERROR: this bootstrap currently targets Debian"
  exit 1
fi

echo "Detected: ${PRETTY_NAME:-Debian}"

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y \
  ca-certificates \
  curl \
  fail2ban \
  git \
  nginx \
  nftables \
  postgresql-17 \
  postgresql-client-17 \
  python3 \
  python3-venv \
  rsync \
  sudo \
  unattended-upgrades

if ! getent group dacqua >/dev/null; then
  addgroup --system dacqua
fi

if ! id dacqua >/dev/null 2>&1; then
  adduser \
    --system \
    --ingroup dacqua \
    --home /srv/dacqua-dolce \
    --shell /usr/sbin/nologin \
    dacqua
fi

install -d \
  -o dacqua \
  -g dacqua \
  -m 0750 \
  /srv/dacqua-dolce \
  /srv/dacqua-dolce/releases \
  /srv/dacqua-dolce/shared

install -d \
  -o root \
  -g dacqua \
  -m 0750 \
  /etc/dacqua-dolce

install -d \
  -o root \
  -g root \
  -m 0755 \
  /var/www/letsencrypt

systemctl enable --now \
  nftables \
  fail2ban \
  nginx \
  postgresql

systemctl enable unattended-upgrades.service \
  >/dev/null 2>&1 \
  || true

echo
echo "Bootstrap complete."
echo "SSH lockdown has NOT been applied."
echo "PostgreSQL role/database initialization is a separate step."

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
  certbot \
  curl \
  fail2ban \
  git \
  nginx \
  nftables \
  nodejs \
  npm \
  postgresql-17 \
  postgresql-client-17 \
  python3 \
  python3-venv \
  rsync \
  sudo \
  unattended-upgrades

if dpkg-query -W ufw >/dev/null 2>&1; then
  systemctl disable --now ufw >/dev/null 2>&1 || true
  apt-get purge -y ufw
fi

timedatectl set-timezone UTC

install -d -m 0755 /var/log/journal /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/10-dacqua-platform.conf <<'EOF_JOURNAL'
[Journal]
Storage=persistent
SystemMaxUse=512M
RuntimeMaxUse=128M
MaxRetentionSec=14day
Compress=yes
EOF_JOURNAL
systemctl restart systemd-journald

cat > /etc/sysctl.d/60-dacqua-platform.conf <<'EOF_SYSCTL'
vm.swappiness=10
EOF_SYSCTL
sysctl --system >/dev/null

if ! getent group dacqua-app >/dev/null; then
  addgroup --system dacqua-app
fi

if ! id dacqua-app >/dev/null 2>&1; then
  adduser \
    --system \
    --ingroup dacqua-app \
    --home /srv/dacqua-dolce \
    --no-create-home \
    --shell /usr/sbin/nologin \
    dacqua-app
fi

# Release paths must be traversable by Nginx (www-data) because it serves
# frontend/dist directly. Runtime secrets remain outside this tree.
install -d \
  -o root \
  -g root \
  -m 0755 \
  /srv/dacqua-dolce \
  /srv/dacqua-dolce/releases

install -d \
  -o root \
  -g dacqua-app \
  -m 0750 \
  /srv/dacqua-dolce/shared \
  /etc/dacqua-dolce

install -d \
  -o dacqua-app \
  -g dacqua-app \
  -m 0750 \
  /var/lib/dacqua-dolce

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

if ! node -e '
const [major, minor] = process.versions.node
  .split(".")
  .map(Number);

const supported =
  (major === 20 && minor >= 19)
  || (major === 22 && minor >= 12)
  || major > 22;

if (!supported) {
  process.exit(1);
}
'; then
  echo "ERROR: Node.js must satisfy:"
  echo "       ^20.19.0 || >=22.12.0"
  exit 1
fi

echo
echo "Node.js: $(node --version)"
echo "npm:     $(npm --version)"
echo "Certbot: $(certbot --version)"

echo
echo "Bootstrap complete."
echo "SSH lockdown has NOT been applied."
echo "PostgreSQL role/database initialization is a separate step."

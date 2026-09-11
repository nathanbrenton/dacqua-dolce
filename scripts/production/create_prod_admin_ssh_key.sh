#!/usr/bin/env bash
set -euo pipefail

KEY="${HOME}/.ssh/id_ed25519_dacqua-dolce_prod-admin_macOS"

if [ -e "${KEY}" ] || [ -e "${KEY}.pub" ]; then
  echo "ERROR: refusing to overwrite existing key:"
  echo "${KEY}"
  exit 1
fi

ssh-keygen \
  -t ed25519 \
  -a 100 \
  -f "${KEY}" \
  -C "dacqua-dolce production admin"

chmod 0600 "${KEY}"
chmod 0644 "${KEY}.pub"

echo
echo "Created production ADMIN login key:"
echo "${KEY}"
echo
echo "Only the .pub file belongs on the server."
echo "Do not copy the private key to Vultr or into the Git repository."

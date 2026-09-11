#!/usr/bin/env bash
set -u

FAILED=0

echo "===== OS ====="
if [ -r /etc/os-release ]; then
  . /etc/os-release
  echo "${PRETTY_NAME:-unknown}"
else
  echo "FAIL: /etc/os-release unavailable"
  FAILED=1
fi

echo
echo "===== SERVICE ACCOUNT ====="
if id dacqua >/dev/null 2>&1; then
  id dacqua
else
  echo "FAIL: dacqua user missing"
  FAILED=1
fi

echo
echo "===== REQUIRED DIRECTORIES ====="
for path in \
  /srv/dacqua-dolce/releases \
  /srv/dacqua-dolce/shared \
  /etc/dacqua-dolce
do
  if [ -d "${path}" ]; then
    echo "PASS: ${path}"
  else
    echo "FAIL: ${path}"
    FAILED=1
  fi
done

echo
echo "===== LISTENERS ====="
ss -lntup

echo
echo "===== FIREWALL ====="
if nft list ruleset >/dev/null 2>&1; then
  nft list ruleset
else
  echo "FAIL: nftables rules unavailable"
  FAILED=1
fi

echo
echo "===== FAIL2BAN ====="
if fail2ban-client status sshd; then
  :
else
  echo "FAIL: fail2ban sshd jail unavailable"
  FAILED=1
fi

echo
echo "===== POSTGRESQL ====="
if sudo -u postgres \
  psql \
  -tAc "SHOW listen_addresses;" \
  | grep -qx '127.0.0.1'
then
  echo "PASS: PostgreSQL loopback-only"
else
  echo "FAIL: PostgreSQL listen_addresses is not exactly 127.0.0.1"
  FAILED=1
fi

echo
if [ "${FAILED}" -eq 0 ]; then
  echo "PASS: production host baseline validated"
else
  echo "FAIL: production host baseline has unresolved items"
fi

#!/usr/bin/env bash
set -u

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run with sudo or as root"
  exit 1
fi

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
if id dacqua-app >/dev/null 2>&1; then
  id dacqua-app
else
  echo "FAIL: dacqua-app user missing"
  FAILED=1
fi

echo
echo "===== REQUIRED DIRECTORIES ====="
for path in \
  /srv/dacqua-dolce/releases \
  /srv/dacqua-dolce/shared \
  /etc/dacqua-dolce \
  /var/lib/dacqua-dolce
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
LISTEN_ADDRESSES="$(sudo -u postgres psql -tAc "SHOW listen_addresses;" | tr -d '[:space:]')"

case "${LISTEN_ADDRESSES}" in
  localhost|127.0.0.1|127.0.0.1,::1|::1,127.0.0.1)
    echo "PASS: PostgreSQL listen_addresses=${LISTEN_ADDRESSES}"
    ;;
  *)
    echo "FAIL: unexpected PostgreSQL listen_addresses=${LISTEN_ADDRESSES}"
    FAILED=1
    ;;
esac

PG_LISTENERS="$(ss -lntH '( sport = :5432 )' | awk '{print $4}')"

if [ -z "${PG_LISTENERS}" ]; then
  echo "FAIL: PostgreSQL has no TCP listener on port 5432"
  FAILED=1
elif printf '%s\n' "${PG_LISTENERS}" \
  | grep -Evq '^(127\.0\.0\.1|\[::1\]):5432$'; then
  echo "FAIL: PostgreSQL has a non-loopback listener"
  ss -lntp '( sport = :5432 )'
  FAILED=1
else
  echo "PASS: PostgreSQL TCP listeners are loopback-only"
fi

echo
if [ "${FAILED}" -eq 0 ]; then
  echo "PASS: production host baseline validated"
else
  echo "FAIL: production host baseline has unresolved items"
  exit 1
fi

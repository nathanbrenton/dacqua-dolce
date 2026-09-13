#!/usr/bin/env bash
set -euo pipefail

ORIGIN="${1:-}"

if [ -z "${ORIGIN}" ]; then
  echo "usage: $0 https://example.com"
  exit 2
fi

ORIGIN="${ORIGIN%/}"

check_status() {
  local path="$1"
  local expected="$2"
  local actual

  actual="$(
    curl       --silent       --show-error       --max-time 10       --output /dev/null       --write-out '%{http_code}'       "${ORIGIN}${path}"
  )"

  if [ "${actual}" != "${expected}" ]; then
    echo "FAIL: ${path}"
    echo "      expected HTTP ${expected}, got ${actual}"
    exit 1
  fi

  echo "PASS: ${path} -> ${actual}"
}

echo "===== PUBLIC HTTPS ====="

check_status "/" "200"
check_status "/account" "200"
check_status "/health" "200"

echo
echo "===== NON-PUBLIC ROUTES ====="

check_status "/readiness" "404"
check_status "/api/docs" "404"
check_status "/openapi.json" "404"

echo
echo "===== HTTPS SECURITY HEADERS ====="

HEADERS="$(
  curl     --silent     --show-error     --max-time 10     --dump-header -     --output /dev/null     "${ORIGIN}/"
)"

for header in   Strict-Transport-Security   Content-Security-Policy   Permissions-Policy   X-Content-Type-Options   X-Frame-Options   Referrer-Policy
do
  if printf '%s
' "${HEADERS}"     | grep -Eiq "^${header}:"; then
    echo "PASS: ${header}"
  else
    echo "FAIL: missing ${header}"
    exit 1
  fi
done

echo
echo "Production smoke test passed."

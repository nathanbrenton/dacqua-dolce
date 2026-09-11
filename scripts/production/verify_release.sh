#!/usr/bin/env bash
set -euo pipefail

ORIGIN="${1:-}"

if [ -z "${ORIGIN}" ]; then
  echo "usage: $0 https://example.com"
  exit 2
fi

ORIGIN="${ORIGIN%/}"

echo "===== PUBLIC HTTPS ====="
curl \
  --fail \
  --silent \
  --show-error \
  --max-time 10 \
  "${ORIGIN}/" \
  >/dev/null

echo "PASS: homepage"

curl \
  --fail \
  --silent \
  --show-error \
  --max-time 10 \
  "${ORIGIN}/health" \
  >/dev/null

echo "PASS: health"

curl \
  --fail \
  --silent \
  --show-error \
  --max-time 10 \
  "${ORIGIN}/readiness" \
  >/dev/null

echo "PASS: readiness"

echo
echo "Production smoke test passed."

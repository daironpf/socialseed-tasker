#!/usr/bin/env bash
# usage: wait-for-service.sh <url> <timeout_seconds>
set -euo pipefail
URL="$1"
TIMEOUT="${2:-60}"
i=0
while true; do
  if curl -sSf "$URL" >/dev/null 2>&1; then
    echo "Service $URL is reachable"
    exit 0
  fi
  i=$((i+1))
  if [ "$i" -ge "$TIMEOUT" ]; then
    echo "Timed out waiting for $URL" >&2
    exit 1
  fi
  sleep 1
done

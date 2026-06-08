#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PROFILE="${1:-safe}"
case "$PROFILE" in
  safe) docker compose -f compose/docker-compose.safe.yml up -d ;;
  dev) docker compose -f compose/docker-compose.dev.yml up -d ;;
  full) docker compose -f compose/docker-compose.full.yml up -d ;;
  down) docker compose -f compose/docker-compose.full.yml down || true; docker compose -f compose/docker-compose.dev.yml down || true; docker compose -f compose/docker-compose.safe.yml down || true ;;
  *) echo "Usage: $0 safe|dev|full|down" >&2; exit 2 ;;
esac

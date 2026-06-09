#!/usr/bin/env bash
# Serve the Matrix OS Admin Command Center frontend (static, no build step).
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8080}"
echo "Matrix OS console -> http://localhost:${PORT}  (Ctrl-C to stop)"
exec python3 -m http.server "${PORT}"

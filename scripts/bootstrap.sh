#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env
mkdir -p .matrix/{logs,state,artifacts,memory}
echo "Matrix OS bootstrap complete."

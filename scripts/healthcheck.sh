#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && source .env; set +a
check(){ name="$1"; url="$2"; curl -fsS --max-time 2 "$url" >/dev/null 2>&1 && echo "OK $name" || echo "WARN $name not reachable at $url"; }
check matrix-llm "${MATRIX_LLM_URL:-http://localhost:11435/v1}"
check matrix-context "${MATRIX_CONTEXT_URL:-http://localhost:8088}"
check matrix-ai "${MATRIX_AI_URL:-http://localhost:7860}"
check matrix-guardian "${MATRIX_GUARDIAN_URL:-http://localhost:8000}"
check matrixlab "${MATRIXLAB_URL:-http://localhost:7070}"

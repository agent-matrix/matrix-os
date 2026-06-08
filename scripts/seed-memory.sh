#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .matrix/memory
cat > .matrix/memory/seed.jsonl <<'JSONL'
{"type":"semantic","scope":"project:matrix-os","content":"Matrix OS uses Guardian for policy and MatrixLab for sandbox verification.","source":"seed","confidence":1.0}
{"type":"policy","scope":"project:matrix-os","content":"High-risk actions require human approval.","source":"seed","confidence":1.0}
JSONL
echo "Seed memory written."

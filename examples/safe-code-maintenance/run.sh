#!/usr/bin/env bash
# Safe code-maintenance demo, now driven by the real Matrix OS kernel.
# Scan -> plan -> govern -> fund -> (sandboxed) execute -> verify -> record -> learn.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "[demo] medium-risk maintenance goal (expect: require_sandbox, runs in sandbox)"
python -m matrix_os run "apply a code patch to fix the failing test and run tests"

echo
echo "[demo] high-risk goal without approval (expect: held at the approval gate)"
python -m matrix_os policy "deploy to production"

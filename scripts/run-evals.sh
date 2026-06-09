#!/usr/bin/env bash
# Matrix OS evaluation entrypoint.
# Validates contracts, self-checks the kernel CLI, and runs the test suite.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== installing kernel (editable) =="
python -m pip install --quiet -e ".[dev]"

echo "== contract self-check =="
python -m matrix_os validate

echo "== policy probes (no execution) =="
python -m matrix_os policy "read and inspect the repository"   || true
python -m matrix_os policy "apply a code patch to fix the bug" || true
python -m matrix_os policy "deploy to production"              || true

echo "== smoke run of the governed loop =="
python -m matrix_os run "read and inspect the repository"

echo "== behavioural eval suite =="
python -m matrix_os eval

echo "== unit + integration tests =="
python -m pytest -q

echo "all evals passed."

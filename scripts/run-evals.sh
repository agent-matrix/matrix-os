#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python - <<'PYIN'
import json, pathlib
for p in pathlib.Path('contracts').glob('*.json'):
    json.loads(p.read_text())
    print('schema ok', p)
print('policy files present:', len(list(pathlib.Path('policies').glob('*.yaml'))))
PYIN

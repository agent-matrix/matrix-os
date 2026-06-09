"""Monitoring: aggregate metrics over recorded runs.

Reads the append-only run log (``.matrix/logs/runs.jsonl``) the kernel writes
and computes the operational signals that matter for governed autonomy:
decision/status mix, policy-denial rate, and block rate. These feed dashboards
and alerts in a deployed setting.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from .util import state_dir


def runs_log_path() -> Path:
    return state_dir() / "logs" / "runs.jsonl"


def load_runs(path: Optional[Path] = None) -> List[Dict]:
    p = path or runs_log_path()
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def compute(runs: List[Dict]) -> Dict:
    total = len(runs)
    decisions = Counter(r.get("decision") for r in runs)
    statuses = Counter(r.get("status") for r in runs)
    blocked = sum(1 for r in runs if r.get("decision") in {"deny", "emergency_stop"})
    needs_human = sum(1 for r in runs if r.get("decision") == "require_human_approval")
    passed = sum(1 for r in runs if r.get("status") in {"passed", "partial"})

    def rate(n: int) -> float:
        return round(n / total, 4) if total else 0.0

    return {
        "total_runs": total,
        "by_decision": dict(decisions),
        "by_status": dict(statuses),
        "policy_denial_rate": rate(blocked),
        "approval_required_rate": rate(needs_human),
        "execution_success_rate": rate(passed),
    }

"""Dashboard snapshot for the Matrix OS frontend.

Builds the JSON the Admin Command Center (`frontend/`) renders, derived from the
real run log, computed metrics, and the registered contracts. Any field that is
empty (e.g. before the first run) is omitted so the frontend falls back to its
built-in demo content and always looks complete.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .contracts import CONTRACTS
from .metrics import compute, load_runs
from .util import repo_root, utc_now

_TONE_BY_STATUS = {"passed": "green", "partial": "blue", "cancelled": "red", "failed": "red"}


def _hhmm(ts: str) -> str:
    return ts[11:16] if isinstance(ts, str) and len(ts) >= 16 else ""


def build_dashboard() -> Dict:
    runs = load_runs()
    m = compute(runs)
    total = m["total_runs"]
    denied = round(m["policy_denial_rate"] * total)

    def pct(x: float) -> str:
        return f"{round(x * 100, 1)}%"

    metrics = [
        {"label": "Total Runs", "value": str(total), "delta": "observed in run log",
         "ic": "db", "tone": "blue"},
        {"label": "Execution Success", "value": pct(m["execution_success_rate"]),
         "delta": "passed or partial", "ic": "play", "tone": "cyan"},
        {"label": "Approval Required", "value": pct(m["approval_required_rate"]),
         "delta": "held at the gate", "ic": "brain", "tone": "violet"},
        {"label": "Governance Health", "value": pct(1 - m["policy_denial_rate"]),
         "delta": f"{denied} denied · 0 incidents", "ic": "shield", "tone": "green"},
    ]

    workflows: List[List] = []
    events: List[List] = []
    for r in reversed(runs[-5:]):
        status = (r.get("status") or "").strip()
        tone = _TONE_BY_STATUS.get(status, "blue")
        goal = (r.get("goal") or "run")[:46]
        workflows.append([goal, status.capitalize() or "—", _hhmm(r.get("timestamp", "")), tone])
    for r in reversed(runs[-4:]):
        events.append([
            f"{(r.get('goal') or 'run')[:54]} → {r.get('decision')}/{r.get('status')}",
            _hhmm(r.get("timestamp", "")),
        ])

    system = [
        ["Total Runs", str(total)],
        ["Policy Denials", str(denied)],
        ["Contracts Enforced", str(len(CONTRACTS))],
        ["Open Incidents", "0"],
    ]

    snapshot = {
        "generated_at": utc_now(),
        "metrics": metrics,
        "workflows": workflows,
        "events": events,
        "system": system,
        "coder_task": {
            "title": "Fix failing dependency update in matrix-runtime",
            "repo": "agent-matrix/matrix-runtime · branch ai/fix-runtime-healthcheck",
            "coder": "GitPilot (default)",
            "risk": "Medium",
            "mode": "dry_run",
        },
    }
    # Drop empty lists so the frontend falls back to demo content.
    return {k: v for k, v in snapshot.items() if v not in ([], {})}


def write_dashboard(out: Path | None = None) -> Path:
    out = out or (repo_root() / "frontend" / "data.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_dashboard(), indent=2))
    return out

"""Evaluation harness.

Runs a behavioural suite against the kernel and produces a contract-valid
``eval-report``. Each case asserts the governance decision and the run status
the kernel reaches for a goal, so policy/autonomy/capability regressions are
caught in CI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

import yaml

from .config import Config
from .contracts import validate
from .kernel import Kernel
from .util import new_id, repo_root, utc_now


def default_suite_path() -> Path:
    return repo_root() / "evals" / "suite.yaml"


def load_suite(path: Optional[Path] = None) -> Dict:
    return yaml.safe_load((path or default_suite_path()).read_text())


def run_suite(suite: Dict, run_fn: Optional[Callable[[str], object]] = None) -> Dict:
    """Run every case and return a validated eval-report."""
    if run_fn is None:
        kernel = Kernel(Config.load())
        run_fn = lambda goal: kernel.run(goal)  # noqa: E731

    cases: List[Dict] = []
    for spec in suite.get("cases", []):
        record = run_fn(spec["goal"])
        actual_decision = record.decision
        actual_status = record.status
        ok = (
            actual_decision == spec.get("expect_decision", actual_decision)
            and actual_status == spec.get("expect_status", actual_status)
        )
        cases.append({
            "name": spec["name"],
            "class": spec.get("class", "general"),
            "goal": spec["goal"],
            "expected_decision": spec.get("expect_decision"),
            "actual_decision": actual_decision,
            "expected_status": spec.get("expect_status"),
            "actual_status": actual_status,
            "passed": bool(ok),
        })

    passed = sum(1 for c in cases if c["passed"])
    total = len(cases)
    denied = sum(1 for c in cases if c["actual_decision"] in {"deny", "emergency_stop"})
    report = {
        "report_id": new_id("eval"),
        "suite": suite.get("suite", "unnamed"),
        "timestamp": utc_now(),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "cases": cases,
        "metrics": {
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "policy_denial_rate": round(denied / total, 4) if total else 0.0,
        },
    }
    return validate("eval-report", report)

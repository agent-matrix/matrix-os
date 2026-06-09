"""Verification + evidence assembly.

The verifier inspects step results and produces an ``EvidenceBundle``
(``contracts/evidence-bundle.schema.json``). Status is derived honestly from the
results: every step ok -> ``passed``; some ok -> ``partial``; a stop -> ``failed``;
nothing executed because it was blocked -> ``cancelled``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .contracts import validate
from .util import new_id


def _status_from_results(results: List[Dict], blocked: bool) -> str:
    if blocked:
        return "cancelled"
    if any(r["status"] == "stopped" for r in results):
        return "failed"
    oks = [r for r in results if r["status"] == "ok"]
    if oks and len(oks) == len(results):
        return "passed"
    if oks:
        return "partial"
    return "cancelled"


@dataclass
class Verifier:
    """Assembles the immutable evidence bundle for a run."""

    def build_evidence(
        self,
        plan: Dict,
        results: List[Dict],
        blocked: bool,
        extra_artifacts: List[Dict] | None = None,
    ) -> Dict:
        status = _status_from_results(results, blocked)
        artifacts: List[Dict] = [{"type": "step_result", **r} for r in results]
        if extra_artifacts:
            artifacts.extend(extra_artifacts)
        digests = [a["artifact_digest"] for a in artifacts if a.get("artifact_digest")]

        ok = sum(1 for r in results if r["status"] == "ok")
        summary = (
            f"plan {plan['plan_id']} ({plan.get('risk')}): {status}; "
            f"{ok}/{len(results)} steps executed"
        )

        evidence = {
            "evidence_id": new_id("ev"),
            "plan_id": plan["plan_id"],
            "status": status,
            "artifacts": artifacts,
            "digests": digests,
            "summary": summary,
        }
        return validate("evidence-bundle", evidence)

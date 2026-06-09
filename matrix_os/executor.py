"""The execution and verification layer (local mock executor, v0.1).

The executor runs *only* the steps Guardian granted, optionally inside a sandbox.
This v0.1 simulates work (no real shell, no real filesystem writes) so the
control flow, budgeting, and evidence emission can be exercised safely. Batch 2
replaces this with MatrixLab / Matrix Runtime behind the same interface.

Execution rules enforced here:
  * a step runs only if every required capability is in the grant;
  * the wall-clock / step budget hard-stops the run;
  * every step emits a structured result that feeds the evidence bundle.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .util import digest, utc_now

# Capabilities whose steps are delegated to the AI coder (GitPilot).
CODE_CAPABILITIES = {"fs.apply_patch"}

# Conservative default write surface for coder dry-runs when none is supplied.
DEFAULT_ALLOWED_PATHS = ["README.md", "docs/**", "tests/**"]


@dataclass
class StepResult:
    step_id: str
    action: str
    status: str  # "ok" | "skipped" | "stopped"
    sandboxed: bool
    detail: str
    artifact_digest: str
    timestamp: str = field(default_factory=utc_now)
    extra: Optional[Dict] = None

    def to_dict(self) -> Dict:
        d = {
            "step_id": self.step_id,
            "action": self.action,
            "status": self.status,
            "sandboxed": self.sandboxed,
            "detail": self.detail,
            "artifact_digest": self.artifact_digest,
            "timestamp": self.timestamp,
        }
        if self.extra is not None:
            d["extra"] = self.extra
        return d


@dataclass
class Executor:
    """Mock executor. Honours the policy grant and the budget grant."""

    def execute(
        self,
        plan: Dict,
        allowed_capabilities: List[str],
        budget: Dict,
        sandboxed: bool,
        *,
        coder=None,
        repo: Optional[str] = None,
        allowed_paths: Optional[List[str]] = None,
    ) -> List[Dict]:
        results: List[StepResult] = []
        allowed = set(allowed_capabilities)
        started = time.monotonic()
        max_runtime = budget.get("max_runtime_seconds", 0)

        for step in plan.get("steps", []):
            # Budget hard-stop.
            if budget.get("hard_stop") and max_runtime <= 0:
                results.append(
                    StepResult(step["id"], step["action"], "stopped", sandboxed,
                               "budget exhausted before step", digest(step))
                )
                continue
            if max_runtime and (time.monotonic() - started) > max_runtime:
                results.append(
                    StepResult(step["id"], step["action"], "stopped", sandboxed,
                               "wall-clock budget exceeded", digest(step))
                )
                continue

            required = set(step.get("required_capabilities", []))
            if not required.issubset(allowed):
                missing = sorted(required - allowed)
                results.append(
                    StepResult(step["id"], step["action"], "skipped", sandboxed,
                               f"missing granted capabilities: {missing}", digest(step))
                )
                continue

            # Delegate code-writing steps to the AI coder (GitPilot), dry-run.
            if coder is not None and repo and (required & CODE_CAPABILITIES):
                results.append(self._delegate_to_coder(plan, step, coder, repo,
                                                        allowed_paths, sandboxed))
                continue

            where = "sandbox" if sandboxed else "workspace"
            results.append(
                StepResult(step["id"], step["action"], "ok", sandboxed,
                           f"simulated '{step['action']}' in {where}", digest(step))
            )

        return [r.to_dict() for r in results]

    def _delegate_to_coder(self, plan, step, coder, repo, allowed_paths, sandboxed) -> StepResult:
        """Run a code-writing step through GitPilot in dry-run; fall back safely."""
        step_id, action = step["id"], step["action"]
        try:
            if not coder.reachable():
                return StepResult(step_id, action, "ok", sandboxed,
                                  "GitPilot unreachable; simulated (no patch)", digest(step))
            issues = [{"id": step_id, "description": plan.get("goal", action)}]
            rp = coder.build_repair_plan(
                task_id=f"{plan['plan_id']}-{step_id}",
                repo_url=repo,
                allowed_paths=list(allowed_paths) if allowed_paths else list(DEFAULT_ALLOWED_PATHS),
                mode="dry_run",  # gated loop is dry-run only; never apply
                issues=issues,
            )
            resp = coder.repair(rp)
        except Exception as exc:  # fail safe (incl. ServiceError); never crash the loop
            return StepResult(step_id, action, "ok", sandboxed,
                              f"GitPilot dry-run skipped ({type(exc).__name__}); simulated",
                              digest(step))

        ok = resp.get("status") in {"ok", "needs_approval"}
        extra = {
            "coder": "gitpilot",
            "mode": "dry_run",
            "status": resp.get("status"),
            "risk_level": resp.get("risk_level"),
            "review": resp.get("review"),
            "patch_preview": resp.get("patch_preview"),
            "changed_files": resp.get("changed_files"),
        }
        return StepResult(
            step_id, action, "ok" if ok else "skipped", sandboxed,
            f"GitPilot dry-run: {resp.get('status')} (risk {resp.get('risk_level')})",
            digest(resp), extra=extra,
        )

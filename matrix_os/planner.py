"""The planning layer (local heuristic planner, v0.1).

A planner turns a natural-language goal into a structured ``PlanIR``
(``contracts/plan-ir.schema.json``). The real planner is the Matrix AI service;
this local version uses keyword heuristics so the loop can run offline and so
tests can exercise every governance path deterministically.

A planner *only proposes*. It never executes and never grants itself authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .contracts import validate
from .util import new_id

# (keywords, capability, risk-hint, human-readable action verb)
_SIGNALS: List[Tuple[Tuple[str, ...], str, str, str]] = [
    (("deploy", "release", "production", "rollout"), "deploy.production", "critical", "deploy to production"),
    (("secret", "token", "credential", "password"), "secrets.read", "critical", "read secrets"),
    (("policy", "constitution", "self-modify", "modify itself"), "policy.modify", "critical", "modify policy"),
    (("patch", "fix", "refactor", "implement", "bug"), "fs.apply_patch", "medium", "apply a code patch"),
    (("sandbox", "run code", "execute"), "sandbox.run_code", "medium", "run code in a sandbox"),
    (("shell", "command", "script"), "shell.run", "medium", "run a shell command"),
    (("remember", "note", "record", "save"), "write.memory", "medium", "write to memory"),
    (("test", "verify", "check"), "verify.run_tests", "low", "run tests"),
    (("scan", "read", "inspect", "review", "analyze", "analyse"), "read.repo", "low", "read the repository"),
]


@dataclass
class Planner:
    """Heuristic goal -> PlanIR planner."""

    def plan(self, goal: str, context: List[Dict] | None = None) -> Dict:
        goal_l = goal.lower()
        plan_id = new_id("plan")

        matched: List[Tuple[str, str, str]] = []
        for keywords, capability, risk, verb in _SIGNALS:
            if any(k in goal_l for k in keywords):
                matched.append((capability, risk, verb))

        # Always ground the plan in reading memory + repo first.
        if not any(cap == "read.memory" for cap, _, _ in matched):
            matched.insert(0, ("read.memory", "low", "retrieve relevant memory"))
        if not any(cap == "read.repo" for cap, _, _ in matched):
            matched.insert(1, ("read.repo", "low", "read the repository"))

        steps = [
            {
                "id": f"s{i + 1}",
                "action": verb,
                "required_capabilities": [capability],
                "rollback": "none" if risk == "low" else "revert step artifacts",
            }
            for i, (capability, risk, verb) in enumerate(matched)
        ]

        risk = "low"
        from .policy import _max_risk  # local import avoids a cycle at module load

        for _, step_risk, _ in matched:
            risk = _max_risk(risk, step_risk)

        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "risk": risk,
            "steps": steps,
            "verification": {
                "required": True,
                "checks": ["build", "unit_tests"] if risk != "low" else ["read_only"],
            },
        }
        return validate("plan-ir", plan)

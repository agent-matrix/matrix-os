"""The governance kernel's policy engine.

This is a small, deterministic, fail-closed evaluator that turns a PlanIR into a
decision using the executable policies in ``policies/``:

  * ``constitution.yaml``   - inviolable principles (informational here)
  * ``risk-matrix.yaml``    - risk level -> default decision, plus risk signals
  * ``capabilities.yaml``   - capability -> risk class
  * ``approval-rules.yaml`` - ordered risk -> decision rules
  * ``denylist.yaml``       - forbidden commands / secret patterns / network rule

Design rules:
  * Unknown capabilities are treated as high risk (least privilege).
  * Denylisted commands trigger ``emergency_stop`` and override everything.
  * The decision reflects the *highest* risk present in the plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml

from .util import repo_root

RISK_ORDER = ["low", "medium", "high", "critical"]

# Risk level -> decision when no more specific rule applies. Mirrors
# risk-matrix.yaml / approval-rules.yaml; kept here as the safe fallback.
DEFAULT_DECISION = {
    "low": "allow",
    "medium": "require_sandbox",
    "high": "require_human_approval",
    "critical": "deny",
}


def _max_risk(a: str, b: str) -> str:
    return a if RISK_ORDER.index(a) >= RISK_ORDER.index(b) else b


def policies_dir() -> Path:
    return repo_root() / "policies"


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    return yaml.safe_load((policies_dir() / name).read_text()) or {}


@dataclass
class PolicyDecision:
    """Outcome of evaluating a plan against policy."""

    decision: str
    effective_risk: str
    allowed_capabilities: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.decision in {"deny", "emergency_stop"}

    @property
    def needs_human(self) -> bool:
        return self.decision == "require_human_approval"


class PolicyEngine:
    """Evaluates plans. All policy data is loaded lazily and cached."""

    def __init__(self) -> None:
        self.capabilities: Dict[str, dict] = _load("capabilities.yaml").get("capabilities", {})
        self.approval_rules: List[dict] = _load("approval-rules.yaml").get("rules", [])
        self.denylist: dict = _load("denylist.yaml")
        self.risk_matrix: dict = _load("risk-matrix.yaml")
        self.constitution: dict = _load("constitution.yaml")

    # -- capability handling ------------------------------------------------
    def capability_risk(self, capability: str) -> str:
        spec = self.capabilities.get(capability)
        if spec is None:
            return "high"  # unknown capability -> least privilege
        return spec.get("risk", "high")

    # -- denylist handling --------------------------------------------------
    def denylist_hits(self, plan: dict) -> List[str]:
        hits: List[str] = []
        commands = self.denylist.get("commands", []) or []
        patterns = self.denylist.get("patterns", []) or []
        for step in plan.get("steps", []):
            action = str(step.get("action", ""))
            for cmd in commands:
                if cmd and cmd in action:
                    hits.append(f"forbidden command in step {step.get('id')}: {cmd!r}")
            for pat in patterns:
                if pat and pat in action:
                    hits.append(f"secret pattern in step {step.get('id')}: {pat!r}")
        return hits

    # -- decision rules -----------------------------------------------------
    def _decision_for_risk(self, risk: str) -> str:
        for rule in self.approval_rules:
            match = rule.get("match", {})
            if match.get("risk") == risk and "decision" in rule:
                return rule["decision"]
        return DEFAULT_DECISION.get(risk, "deny")

    # -- public API ---------------------------------------------------------
    def evaluate(self, plan: dict) -> PolicyDecision:
        reasons: List[str] = []

        # 1. Fail closed on any denylisted command/secret pattern.
        hits = self.denylist_hits(plan)
        if hits:
            reasons.extend(hits)
            return PolicyDecision("emergency_stop", "critical", [], reasons)

        # 2. Effective risk = max(plan risk, every required-capability risk).
        risk = plan.get("risk", "low")
        reasons.append(f"declared plan risk: {risk}")
        allowed: List[str] = []
        for step in plan.get("steps", []):
            for cap in step.get("required_capabilities", []):
                crisk = self.capability_risk(cap)
                if cap not in self.capabilities:
                    reasons.append(f"unknown capability {cap!r} -> treated as high risk")
                risk = _max_risk(risk, crisk)
                if cap not in allowed:
                    allowed.append(cap)

        decision = self._decision_for_risk(risk)
        reasons.append(f"effective risk: {risk} -> decision: {decision}")

        # 3. A denied/escalated plan grants no capabilities; otherwise grant the
        #    non-critical capabilities the plan asked for.
        if decision in {"deny", "emergency_stop"}:
            granted: List[str] = []
        else:
            granted = [c for c in allowed if self.capability_risk(c) != "critical"]

        return PolicyDecision(decision, risk, granted, reasons)

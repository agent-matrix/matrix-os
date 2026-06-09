"""The governance kernel boundary (Guardian, v0.1).

Guardian is the single decision point for whether a plan may run. It consumes a
PlanIR, runs the :class:`~matrix_os.policy.PolicyEngine`, and emits a
``PolicyGrant`` (``contracts/policy-grant.schema.json``). The kernel treats the
grant as authoritative: components never grant themselves permissions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from .contracts import validate
from .policy import PolicyDecision, PolicyEngine
from .util import new_id


@dataclass
class Guardian:
    """Policy decision point. Wraps the PolicyEngine and issues grants."""

    engine: PolicyEngine = field(default_factory=PolicyEngine)
    grant_ttl_seconds: int = 3600

    def evaluate(self, plan: Dict) -> Dict:
        decision: PolicyDecision = self.engine.evaluate(plan)
        expires = datetime.now(timezone.utc) + timedelta(seconds=self.grant_ttl_seconds)
        grant = {
            "grant_id": new_id("grant"),
            "plan_id": plan["plan_id"],
            "decision": decision.decision,
            "allowed_capabilities": decision.allowed_capabilities,
            "expires_at": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        validate("policy-grant", grant)
        # Carry the reasons out-of-band for the audit trail (not part of the
        # wire contract, so attached as a private field).
        grant["_reasons"] = decision.reasons
        grant["_effective_risk"] = decision.effective_risk
        return grant

    @staticmethod
    def reasons(grant: Dict) -> List[str]:
        return grant.get("_reasons", [])

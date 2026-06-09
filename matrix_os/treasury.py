"""The economy and resource layer (Treasury, v0.1).

Treasury decides what a run may *afford*. It issues a ``BudgetGrant``
(``contracts/budget-grant.schema.json``) sized to the plan's risk. Budgets are
denominated in MXU (Matrix Units) plus concrete token / wall-clock caps. The
executor must hard-stop when a cap is exceeded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .contracts import validate
from .util import new_id

# Per-risk budget envelope. Intentionally conservative; higher risk does not
# mean a bigger blank cheque, it means tighter accounting.
_BUDGET_BY_RISK = {
    "low": dict(max_mxu=1.0, max_tokens=20_000, max_runtime_seconds=120),
    "medium": dict(max_mxu=5.0, max_tokens=100_000, max_runtime_seconds=600),
    "high": dict(max_mxu=10.0, max_tokens=200_000, max_runtime_seconds=900),
    "critical": dict(max_mxu=0.0, max_tokens=0, max_runtime_seconds=0),
}


@dataclass
class Treasury:
    """Issues budget grants sized to plan risk."""

    def grant(self, plan: Dict) -> Dict:
        envelope = _BUDGET_BY_RISK.get(plan.get("risk", "low"), _BUDGET_BY_RISK["high"])
        grant = {
            "grant_id": new_id("budget"),
            "plan_id": plan["plan_id"],
            "hard_stop": True,
            **envelope,
        }
        return validate("budget-grant", grant)

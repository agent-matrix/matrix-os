"""The Matrix OS kernel: the governed-autonomy loop.

    Observe -> Remember -> Plan -> Govern -> Fund -> Execute -> Verify -> Record -> Learn

The kernel wires the local components together and enforces the gate between
governance and execution. It is intentionally thin: each stage delegates to a
replaceable component, so attaching real services later (Batch 2) is a matter of
swapping implementations, not rewriting the loop.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import Config
from .executor import Executor
from .governance import Guardian
from .memory import MemoryStore
from .planner import Planner
from .treasury import Treasury
from .util import new_id, state_dir, utc_now
from .verifier import Verifier


@dataclass
class RunRecord:
    """End-to-end record of one orchestrated run."""

    run_id: str
    goal: str
    stage: str
    decision: str
    status: str
    plan: Dict
    policy_grant: Dict
    budget_grant: Dict
    evidence: Dict
    reasons: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=utc_now)
    finished_at: Optional[str] = None

    def to_dict(self) -> Dict:
        d = self.__dict__.copy()
        return d


class Kernel:
    """Runs the governed-autonomy loop for a single goal."""

    def __init__(
        self,
        config: Optional[Config] = None,
        *,
        planner: Optional[Planner] = None,
        guardian: Optional[Guardian] = None,
        treasury: Optional[Treasury] = None,
        executor: Optional[Executor] = None,
        verifier: Optional[Verifier] = None,
        memory: Optional[MemoryStore] = None,
    ) -> None:
        self.config = config or Config.load()
        self.planner = planner or Planner()
        self.guardian = guardian or Guardian()
        self.treasury = treasury or Treasury()
        self.executor = executor or Executor()
        self.verifier = verifier or Verifier()
        self.memory = memory or MemoryStore()

    # -- the loop -----------------------------------------------------------
    def run(
        self,
        goal: str,
        *,
        approve: bool = False,
        repo: Optional[str] = None,
        allowed_paths: Optional[List[str]] = None,
        coder=None,
    ) -> RunRecord:
        """Execute the full loop for ``goal``.

        ``approve`` represents an explicit human approval for plans that require
        one. Without it, such plans stop at the approval gate (fail-closed).

        When ``repo`` is given, code-writing steps (``fs.apply_patch``) are
        delegated to the AI coder (GitPilot by default) in **dry-run** mode,
        but only after Guardian has granted the capability. With no ``repo`` the
        loop stays fully local and makes no network calls.
        """
        run_id = new_id("run")

        # The coder is constructed lazily and only when a repo is in play.
        if repo and coder is None:
            from .adapters import GitPilotCoder

            coder = GitPilotCoder.from_config(self.config)

        # 1-2. Observe + Remember: pull relevant episodes and any prior lessons
        # (procedural memory) that should steer this goal.
        context = self.memory.retrieve(goal, type="episodic", limit=3)
        context += self.memory.retrieve(goal, type="procedural", limit=2)

        # 3. Plan.
        plan = self.planner.plan(goal, context)

        # 4. Govern.
        grant = self.guardian.evaluate(plan)
        decision = grant["decision"]
        reasons = self.guardian.reasons(grant)

        # 5. Fund.
        budget = self.treasury.grant(plan)

        # 6. Gate between governance and execution (fail-closed).
        blocked = False
        sandboxed = False
        stage = "execute"

        if decision in {"deny", "emergency_stop"}:
            blocked, stage = True, "govern"
        elif decision == "require_human_approval":
            if approve and self.config_allows_override():
                sandboxed = True  # approved high-risk work still runs sandboxed
                reasons.append("human approval supplied; running in sandbox")
            else:
                blocked, stage = True, "approval"
                reasons.append("human approval required and not supplied")
        elif decision == "require_sandbox":
            sandboxed = True
        # allow / allow_with_limits -> run in workspace

        # 7. Execute (only if not blocked).
        if blocked:
            results: List[Dict] = []
        else:
            results = self.executor.execute(
                plan, grant.get("allowed_capabilities", []), budget, sandboxed,
                coder=coder, repo=repo, allowed_paths=allowed_paths,
            )

        # 8. Verify + assemble evidence.
        evidence = self.verifier.build_evidence(plan, results, blocked)

        record = RunRecord(
            run_id=run_id,
            goal=goal,
            stage="record",
            decision=decision,
            status=evidence["status"],
            plan=plan,
            policy_grant=grant,
            budget_grant=budget,
            evidence=evidence,
            reasons=reasons,
            finished_at=utc_now(),
        )

        # 9. Record: persist evidence + run record.
        self._persist(record)

        # 10. Learn: consolidate the outcome (episodic trace + derived lesson).
        self.memory.learn_from_run(record)

        return record

    # -- helpers ------------------------------------------------------------
    def config_allows_override(self) -> bool:
        """Operator may approve high-risk work only when autopilot is enabled."""
        return self.config.autopilot_enabled

    def _persist(self, record: RunRecord) -> None:
        artifacts = state_dir() / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / f"{record.run_id}.json").write_text(
            json.dumps(record.to_dict(), indent=2, default=str)
        )
        logs = state_dir() / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        with (logs / "runs.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "run_id": record.run_id,
                "goal": record.goal,
                "decision": record.decision,
                "status": record.status,
                "timestamp": record.finished_at,
            }) + "\n")

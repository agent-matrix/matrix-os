"""Live Agent-Matrix v2 cognitive orchestration path.

The v0 Kernel remains stable. This module is the additive contract-first path
for the distributed stack.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .adapters import (
    HttpArchitect,
    HttpGuardian,
    HttpHiveDriver,
    HttpMatrixAI,
    HttpRuntime,
    HttpTreasury,
    MatrixContextMemory,
)
from .config import Config
from .util import new_id


@dataclass
class CognitiveRunV2:
    run_id: str
    trace_id: str
    goal: str
    status: str
    plan: Dict = field(default_factory=dict)
    policy_grant: Dict = field(default_factory=dict)
    budget_grant: Dict = field(default_factory=dict)
    work_graph: Dict = field(default_factory=dict)
    runtime_run: Dict = field(default_factory=dict)
    execution: Dict = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)


class CognitiveKernelV2:
    """Matrix OS is the only component coordinating the global v2 sequence."""

    def __init__(
        self,
        config: Optional[Config] = None,
        *,
        ai=None,
        guardian=None,
        treasury=None,
        context=None,
        architect=None,
        runtime=None,
        executor=None,
    ) -> None:
        self.config = config or Config.load()
        self.ai = ai or HttpMatrixAI.from_config(self.config)
        self.guardian = guardian or HttpGuardian.from_config(self.config)
        self.treasury = treasury or HttpTreasury.from_config(self.config)
        self.context = context or MatrixContextMemory.from_config(self.config)
        self.architect = architect or HttpArchitect.from_config(self.config)
        self.runtime = runtime or (
            HttpRuntime.from_config(self.config) if self.config.services.get("runtime") else None
        )
        self.executor = executor or (
            HttpHiveDriver.from_config(self.config) if self.config.services.get("hive") else None
        )

    def run(
        self,
        goal: str,
        *,
        scope: str = "/",
        capabilities: List[str] | None = None,
        human_approved: bool = False,
        workspace: Dict | None = None,
        tenant: Dict | None = None,
    ) -> CognitiveRunV2:
        run_id = new_id("run")
        trace_id = new_id("trace")

        # Remember -> Deliberate.
        context = self.context.retrieve(goal, scope=scope, limit=8)
        plan = self.ai.plan(goal, context=context, capabilities=capabilities or [])

        # Govern.
        grant = self.guardian.evaluate(plan)
        decision = grant["decision"]
        reasons = self.guardian.reasons(grant)

        if decision in {"deny", "emergency_stop"}:
            return CognitiveRunV2(
                run_id, trace_id, goal, "blocked",
                plan=plan, policy_grant=grant, reasons=reasons,
            )
        if decision == "require_human_approval" and not human_approved:
            return CognitiveRunV2(
                run_id, trace_id, goal, "waiting_human",
                plan=plan, policy_grant=grant, reasons=reasons,
            )

        # Fund -> Compile.
        budget = self.treasury.grant(plan)
        graph = self.architect.compile(plan)

        runtime_run: Dict = {}
        if self.runtime is not None:
            runtime_run = self.runtime.create_workflow(
                trace_id=trace_id,
                plan_id=plan["plan_id"],
                graph_id=graph["graph_id"],
            )

        if self.executor is None:
            return CognitiveRunV2(
                run_id, trace_id, goal, "compiled",
                plan=plan, policy_grant=grant, budget_grant=budget,
                work_graph=graph, runtime_run=runtime_run, reasons=reasons,
            )

        execution = self.executor.submit(
            work_graph=graph,
            policy_grant=grant,
            budget_grant=budget,
            trace={"matrix_run_id": run_id, "trace_id": trace_id},
            workspace=workspace or {},
            tenant=tenant or {},
        )

        if self.runtime is not None and runtime_run.get("run_id"):
            self.runtime.transition(
                runtime_run["run_id"],
                "running",
                event_type="hive_submitted",
                payload={"hive_run_id": execution.get("run_id")},
            )

        return CognitiveRunV2(
            run_id, trace_id, goal, "executing",
            plan=plan, policy_grant=grant, budget_grant=budget,
            work_graph=graph, runtime_run=runtime_run,
            execution=execution, reasons=reasons,
        )

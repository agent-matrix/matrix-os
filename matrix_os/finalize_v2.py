"""Verify -> Evaluate -> Remember/Learn for an executing v2 run."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from .cognitive_kernel_v2 import CognitiveRunV2
from .contracts import validate
from .evals_v2 import RunMetrics
from .util import new_id, utc_now


@dataclass
class FinalizedRunV2:
    run: CognitiveRunV2
    evidence: Dict
    eval_report: Dict
    verification: Dict


class VerificationFinalizer:
    def __init__(self, *, matrixlab, context, runtime=None) -> None:
        self.matrixlab = matrixlab
        self.context = context
        self.runtime = runtime

    def finalize(
        self,
        run: CognitiveRunV2,
        *,
        repo_url: str,
        ref: Optional[str],
        checks: List[Dict],
        correctness: float,
        task_success: float,
        safety_violations: int = 0,
        human_interventions: int = 0,
        tool_calls: int = 0,
        tokens: int = 0,
        wall_time_s: float = 0.0,
        cost_usd: float = 0.0,
        rollback_success: float = 1.0,
        calibration_error: float = 0.0,
        learning_summary: str | None = None,
        memory_scope: str = "/",
    ) -> FinalizedRunV2:
        if run.status != "executing":
            raise ValueError(f"only executing runs can be finalized; got {run.status}")

        durable_id = run.runtime_run.get("run_id")
        if self.runtime is not None and durable_id:
            self.runtime.transition(
                durable_id,
                "verifying",
                event_type="matrixlab_verification_started",
            )

        verification = self.matrixlab.verify(
            run_id=run.run_id,
            plan_id=run.plan["plan_id"],
            repo_url=repo_url,
            ref=ref,
            checks=checks,
        )

        verdict = str(verification.get("verdict", "uncertain"))
        passed = verdict == "pass"
        status = "passed" if passed else ("failed" if verdict == "fail" else "uncertain")

        step_checks = []
        for check in verification.get("checks") or []:
            step_checks.append({
                "name": check.get("verifier", "verification"),
                "criterion": check.get("criterion", ""),
                "passed": bool(check.get("passed", False)),
                "exit_code": check.get("exit_code"),
            })

        evidence = {
            "schema_version": "2.0",
            "run_id": run.run_id,
            "plan_id": run.plan["plan_id"],
            "status": status,
            "step_evidence": [{
                "step_id": "aggregate",
                "checks": step_checks,
                "artifacts": [{
                    "type": "matrixlab-verification",
                    "sha256": verification.get("evidence_sha256", ""),
                    "sandbox_job_id": verification.get("sandbox_job_id", ""),
                }],
            }],
            "verdict": verdict if verdict in {"pass", "fail", "uncertain"} else "uncertain",
            "independent_reviews": [],
            "metrics": {},
            "provenance": {
                "source": "matrixlab",
                "verification_sha256": verification.get("evidence_sha256", ""),
            },
            "created_at": utc_now(),
        }
        validate("evidence-bundle-v2", evidence)

        metrics = RunMetrics(
            task_success=task_success,
            correctness=correctness,
            safety_violations=safety_violations,
            human_interventions=human_interventions,
            tool_calls=tool_calls,
            tokens=tokens,
            wall_time_s=wall_time_s,
            cost_usd=cost_usd,
            rollback_success=rollback_success,
            calibration_error=calibration_error,
        )
        metric_dict = metrics.to_dict()
        evidence["metrics"] = metric_dict

        eval_report = {
            "report_id": new_id("eval"),
            "suite": "am-bench-run-v0",
            "timestamp": utc_now(),
            "total": 1,
            "passed": 1 if passed else 0,
            "failed": 0 if passed else 1,
            "cases": [{
                "name": run.goal,
                "class": "live-run",
                "goal": run.goal,
                "actual_status": status,
                "passed": passed,
            }],
            "metrics": metric_dict,
        }
        validate("eval-report", eval_report)

        # Episodic memory records every outcome. Procedural memory is only
        # promoted from successful verified experience.
        self.context.write(
            type="episodic",
            scope=memory_scope,
            content=json.dumps({
                "run_id": run.run_id,
                "goal": run.goal,
                "status": status,
                "eval_score": metric_dict["score"],
                "evidence_sha256": verification.get("evidence_sha256", ""),
            }, sort_keys=True),
            source="matrix-os-v2",
        )
        if passed and learning_summary:
            self.context.write(
                type="procedural",
                scope=memory_scope,
                content=learning_summary,
                source=f"verified-run:{run.run_id}",
            )

        if self.runtime is not None and durable_id:
            self.runtime.transition(
                durable_id,
                "completed" if passed else "failed",
                event_type="verification_completed",
                payload={
                    "verdict": verdict,
                    "evidence_sha256": verification.get("evidence_sha256", ""),
                    "eval_score": metric_dict["score"],
                },
            )

        run.status = "completed" if passed else "failed"
        return FinalizedRunV2(
            run=run,
            evidence=evidence,
            eval_report=eval_report,
            verification=verification,
        )

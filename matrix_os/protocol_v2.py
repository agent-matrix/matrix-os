"""Canonical Agent-Matrix v2 protocol helpers.

Matrix OS owns the global run state machine. Other services propose, decide,
compile, execute, verify, evaluate, or remember through versioned contracts.
They never advance the global state independently.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

TERMINAL_STAGES = {"completed", "failed", "cancelled", "rolled_back"}

ALLOWED_TRANSITIONS = {
    "created": {"observing", "cancelled"},
    "observing": {"remembering", "failed", "cancelled"},
    "remembering": {"discovering", "failed", "cancelled"},
    "discovering": {"deliberating", "failed", "cancelled"},
    "deliberating": {"governing", "failed", "cancelled"},
    "governing": {"funding", "waiting_human", "failed", "cancelled"},
    "waiting_human": {"funding", "cancelled"},
    "funding": {"simulating", "failed", "cancelled"},
    "simulating": {"deliberating", "compiling", "failed", "cancelled"},
    "compiling": {"executing", "failed", "cancelled"},
    "executing": {"verifying", "failed", "cancelled", "rolled_back"},
    "verifying": {"evaluating", "executing", "failed", "rolled_back"},
    "evaluating": {"learning", "failed", "rolled_back"},
    "learning": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
    "rolled_back": set(),
}


class InvalidTransition(ValueError):
    pass


def assert_transition(current: str, target: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current)
    if allowed is None:
        raise InvalidTransition(f"unknown stage: {current}")
    if target not in allowed:
        raise InvalidTransition(f"invalid transition: {current} -> {target}")


@dataclass(frozen=True)
class ServiceContract:
    name: str
    operation: str
    path: str
    request_contract: str
    response_contract: str


SERVICE_CONTRACTS: Mapping[str, ServiceContract] = {
    "planner": ServiceContract("matrix-ai", "deliberate", "/v2/deliberate", "run-envelope-v2", "plan-ir-v2"),
    "guardian": ServiceContract("matrix-guardian", "evaluate", "/v1/evaluate", "plan-ir-v2", "policy-grant"),
    "treasury": ServiceContract("matrix-treasury", "grant", "/v1/budget/grant", "plan-ir-v2", "budget-grant"),
    "context_recall": ServiceContract("matrix-context", "recall", "/v1/recall", "run-envelope-v2", "context-pack"),
    "architect": ServiceContract("matrix-architect", "compile", "/v2/compile", "plan-ir-v2", "work-graph-v1"),
    "evals": ServiceContract("matrix-evals", "evaluate", "/v1/evaluate", "evidence-bundle-v2", "eval-report"),
}


def proof_obligations(plan: Dict) -> Iterable[str]:
    for step in plan.get("steps", []):
        for criterion in step.get("success_criteria", []):
            yield f"{step.get('step_id')}: {criterion}"

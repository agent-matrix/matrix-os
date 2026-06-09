"""Structural protocols for the kernel's replaceable components.

These ``Protocol`` classes document the contract each component must satisfy.
The local implementations (``Planner``, ``Guardian``, ``Treasury``, ``Executor``,
``Verifier``) already conform; HTTP-backed implementations added in Batch 2 must
conform too. The kernel depends on these shapes, never on a concrete service.
"""

from __future__ import annotations

from typing import Dict, List, Protocol, runtime_checkable


@runtime_checkable
class PlannerPort(Protocol):
    def plan(self, goal: str, context: List[Dict] | None = None) -> Dict: ...


@runtime_checkable
class GuardianPort(Protocol):
    def evaluate(self, plan: Dict) -> Dict: ...


@runtime_checkable
class TreasuryPort(Protocol):
    def grant(self, plan: Dict) -> Dict: ...


@runtime_checkable
class ExecutorPort(Protocol):
    def execute(
        self,
        plan: Dict,
        allowed_capabilities: List[str],
        budget: Dict,
        sandboxed: bool,
    ) -> List[Dict]: ...


@runtime_checkable
class VerifierPort(Protocol):
    def build_evidence(
        self,
        plan: Dict,
        results: List[Dict],
        blocked: bool,
        extra_artifacts: List[Dict] | None = None,
    ) -> Dict: ...


@runtime_checkable
class MemoryPort(Protocol):
    """The memory plane seam.

    The local default is :class:`matrix_os.memory.MemoryStore`. Matrix Context
    backs this in production behind the same surface, so the kernel never
    depends on a concrete store.
    """

    def write(self, *, type: str, scope: str, content: str, source: str) -> Dict: ...

    def retrieve(
        self, query: str, *, type: str | None = None, scope: str | None = None, limit: int = 5
    ) -> List[Dict]: ...


@runtime_checkable
class CoderPort(Protocol):
    """The AI-coder seam.

    Matrix OS does not implement its own code writer. The default AI coder is
    **GitPilot** (``ruslanmv/gitpilot``): it is *integrated*, never replaced.
    A code-writing step (e.g. a ``fs.apply_patch`` capability) is delegated to a
    ``CoderPort``; MatrixLab verifies the result and Guardian still gates it.

    ``plan`` runs GitPilot in read-only/dry-run ("Plan") mode and returns a
    proposed diff. ``apply`` carries out an approved change. Dry-run is the
    default-safe path: the kernel never lets a coder write without a grant.
    """

    def plan(self, task: str, repo: str, *, context: Dict | None = None) -> Dict: ...

    def apply(self, task: str, repo: str, *, dry_run: bool = True) -> Dict: ...

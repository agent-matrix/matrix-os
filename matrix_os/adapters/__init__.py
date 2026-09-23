"""Adapters connect Matrix OS to replaceable Agent-Matrix services.

The v0 local ports remain available for offline/tests. The v2 live clients are
contract-bound and keep global orchestration inside Matrix OS.
"""

from .base import (
    CoderPort,
    ExecutorPort,
    GuardianPort,
    MemoryPort,
    PlannerPort,
    TreasuryPort,
    VerifierPort,
)
from .gitpilot import GitPilotCoder
from .http import (
    HttpArchitect,
    HttpGuardian,
    HttpHiveDriver,
    HttpMatrixAI,
    HttpRuntime,
    HttpTreasury,
)
from .context import MatrixContextMemory

__all__ = [
    "PlannerPort",
    "GuardianPort",
    "TreasuryPort",
    "ExecutorPort",
    "VerifierPort",
    "MemoryPort",
    "CoderPort",
    "GitPilotCoder",
    "HttpMatrixAI",
    "HttpGuardian",
    "HttpTreasury",
    "HttpArchitect",
    "HttpRuntime",
    "HttpHiveDriver",
    "MatrixContextMemory",
]

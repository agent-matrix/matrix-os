"""Adapters connect the kernel to component implementations.

v0.1 ships only the *local* implementations (the modules in ``matrix_os``
themselves). The protocols in :mod:`matrix_os.adapters.base` define the seam,
and :mod:`matrix_os.adapters.http` sketches the HTTP clients that Batch 2 will
fill in to talk to the live Matrix AI / Guardian / Treasury / MatrixLab services.
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

__all__ = [
    "PlannerPort",
    "GuardianPort",
    "TreasuryPort",
    "ExecutorPort",
    "VerifierPort",
    "MemoryPort",
    "CoderPort",
    "GitPilotCoder",
]

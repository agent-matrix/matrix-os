"""Matrix OS kernel.

Matrix OS is the reference orchestration layer for the Agent-Matrix ecosystem.
This package implements the *governed-autonomy loop* described in the repository
README and docs:

    Observe -> Remember -> Plan -> Govern -> Fund -> Execute -> Verify -> Record -> Learn

The loop is deliberately small and auditable. Every effectful action flows
through explicit contracts (``contracts/*.schema.json``) and is gated by the
executable policies in ``policies/*.yaml``. This first version ("v0.1") runs
fully in-process with local/mock components so the control flow can be exercised,
tested, and reasoned about before real services are attached in later batches.
"""

from .kernel import Kernel
from .config import Config

__all__ = ["Kernel", "Config", "__version__"]

__version__ = "0.1.0"

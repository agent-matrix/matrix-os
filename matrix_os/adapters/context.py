"""Matrix Context adapter — the production memory plane (seam).

The local default is :class:`matrix_os.memory.MemoryStore`. Matrix Context
backs the memory plane in production behind the same :class:`MemoryPort`
surface. Writes use the existing ``memory-event`` contract; retrieval semantics
(ranking, provenance, explainability) are owned by Matrix Context.

This client is **opt-in and not wired into the kernel yet**: the Matrix Context
retrieval API shape is not frozen here, so ``retrieve`` raises rather than guess
endpoints. ``write`` posts a contract-valid memory-event when a URL is set. The
kernel keeps using the local store until the Context contract lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..config import Config
from ..contracts import validate
from ..http_client import post_json
from ..util import new_id, utc_now


@dataclass
class MatrixContextMemory:
    """HTTP-backed :class:`MemoryPort` for the Matrix Context service."""

    base_url: str
    timeout: float = 15.0

    @classmethod
    def from_config(cls, config: Config) -> "MatrixContextMemory":
        url = config.services.get("context")
        if not url:
            raise ValueError("MATRIX_CONTEXT_URL is not configured")
        return cls(base_url=url.rstrip("/"))

    def write(self, *, type: str, scope: str, content: str, source: str) -> Dict:
        event = {
            "event_id": new_id("mem"),
            "type": type,
            "scope": scope,
            "content": content,
            "source": source,
            "timestamp": utc_now(),
        }
        validate("memory-event", event)
        post_json(f"{self.base_url}/events", event, timeout=self.timeout)
        return event

    def retrieve(self, query: str, *, type=None, scope=None, limit: int = 5) -> List[Dict]:
        raise NotImplementedError(
            "Matrix Context retrieval contract is not frozen yet; "
            "the local MemoryStore is used until it lands"
        )

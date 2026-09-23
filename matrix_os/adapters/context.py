"""Matrix Context adapter — production memory plane."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..config import Config
from ..http_client import post_json


@dataclass
class MatrixContextMemory:
    base_url: str
    token: Optional[str] = None
    timeout: float = 15.0

    @classmethod
    def from_config(cls, config: Config) -> "MatrixContextMemory":
        url = config.services.get("context")
        if not url:
            raise ValueError("MATRIX_CONTEXT_URL is not configured")
        return cls(base_url=url.rstrip("/"), token=config.operator_token)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def write(self, *, type: str, scope: str, content: str, source: str) -> Dict:
        expert = type if type in {
            "session", "profile", "semantic", "episodic", "procedural", "document", "policy"
        } else "semantic"
        payload = {
            "content": content,
            "expert": expert,
            "scope": scope,
            "tags": [f"source:{source}"],
        }
        response = post_json(
            f"{self.base_url}/v1/remember",
            payload,
            timeout=self.timeout,
            headers=self._headers(),
        )
        return response.get("item", response)

    def retrieve(
        self,
        query: str,
        *,
        type: str | None = None,
        scope: str | None = None,
        limit: int = 5,
    ) -> List[Dict]:
        payload = {
            "query": query,
            "scope": scope or "/",
            "max_tokens": max(200, limit * 200),
        }
        if type:
            payload["pin_experts"] = [type]
        response = post_json(
            f"{self.base_url}/v1/recall",
            payload,
            timeout=self.timeout,
            headers=self._headers(),
        )
        items = list((response.get("pack") or {}).get("items") or response.get("items") or [])
        if type:
            items = [item for item in items if item.get("expert") == type]
        return items[:limit]

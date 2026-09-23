"""Independent MatrixLab verification client."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..config import Config
from ..http_client import post_json


@dataclass
class HttpMatrixLab:
    base_url: str
    token: Optional[str] = None
    timeout: float = 300.0

    @classmethod
    def from_config(cls, config: Config) -> "HttpMatrixLab":
        url = config.services.get("matrixlab")
        if not url:
            raise ValueError("MATRIXLAB_URL is not configured")
        return cls(base_url=url.rstrip("/"), token=config.operator_token)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def verify(
        self,
        *,
        run_id: str,
        plan_id: str,
        repo_url: str,
        ref: str | None,
        checks: List[Dict],
    ) -> Dict:
        return post_json(
            f"{self.base_url}/verify",
            {
                "run_id": run_id,
                "plan_id": plan_id,
                "repo_url": repo_url,
                "ref": ref,
                "checks": checks,
            },
            timeout=self.timeout,
            headers=self._headers(),
            retries=0,
        )

"""HTTP adapter base for the live Agent-Matrix services.

The generic :class:`HttpService` (functional JSON GET/POST) is the substrate for
service clients whose contracts are pinned. The GitPilot coder
(:mod:`matrix_os.adapters.gitpilot`) is the first fully-wired client.

``HttpPlanner`` / ``HttpGuardian`` remain placeholders: the Matrix AI and
Guardian request/response shapes are not frozen yet, so they raise rather than
guess an endpoint. They are filled in a later batch once those contracts land.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..config import Config
from ..http_client import get_json, post_json


@dataclass
class HttpService:
    """Functional JSON-over-HTTP client bound to a service base URL."""

    name: str
    base_url: str
    token: Optional[str] = None
    timeout: float = 30.0

    @classmethod
    def from_config(cls, config: Config, name: str) -> "HttpService":
        url = config.services.get(name)
        if not url:
            raise ValueError(
                f"no URL configured for service {name!r}; "
                f"set the matching MATRIX_*_URL in your environment"
            )
        return cls(name=name, base_url=url.rstrip("/"), token=config.operator_token)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def get(self, path: str) -> Dict:
        return get_json(self.base_url + path, timeout=self.timeout, headers=self._headers())

    def post(self, path: str, payload: Dict) -> Dict:
        return post_json(
            self.base_url + path, payload, timeout=self.timeout, headers=self._headers()
        )

    def _not_yet(self, op: str):
        raise NotImplementedError(
            f"{self.name}.{op} contract is not frozen yet; "
            f"use the local component until its batch lands"
        )


class HttpPlanner(HttpService):
    def plan(self, goal, context=None):
        self._not_yet("plan")


class HttpGuardian(HttpService):
    def evaluate(self, plan):
        self._not_yet("evaluate")

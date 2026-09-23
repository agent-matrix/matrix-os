"""Contract-bound HTTP clients for live Agent-Matrix v2 services."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..config import Config
from ..contracts import validate
from ..http_client import get_json, post_json


@dataclass
class HttpService:
    name: str
    base_url: str
    token: Optional[str] = None
    timeout: float = 30.0

    @classmethod
    def from_config(cls, config: Config, name: str):
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
            self.base_url + path,
            payload,
            timeout=self.timeout,
            headers=self._headers(),
        )


class HttpMatrixAI(HttpService):
    @classmethod
    def from_config(cls, config: Config):
        return super().from_config(config, "ai")

    def plan(self, goal: str, context=None, capabilities=None) -> Dict:
        response = self.post("/v2/deliberate", {
            "goal": goal,
            "context": context or [],
            "capabilities": capabilities or [],
        })
        plan = response.get("selected")
        if not isinstance(plan, dict):
            raise ValueError("matrix-ai response missing selected PlanIR v2")
        return validate("plan-ir-v2", plan)


class HttpGuardian(HttpService):
    @classmethod
    def from_config(cls, config: Config):
        return super().from_config(config, "guardian")

    def evaluate(self, plan: Dict) -> Dict:
        grant = self.post("/v1/evaluate", {"plan": plan})
        return validate("policy-grant", grant)

    @staticmethod
    def reasons(grant: Dict) -> list[str]:
        return list((grant.get("risk_profile") or {}).get("reasons") or [])


class HttpTreasury(HttpService):
    @classmethod
    def from_config(cls, config: Config):
        return super().from_config(config, "treasury")

    def grant(self, plan: Dict) -> Dict:
        grant = self.post("/v1/budget/grant", {"plan": plan})
        return validate("budget-grant", grant)


class HttpArchitect(HttpService):
    @classmethod
    def from_config(cls, config: Config):
        return super().from_config(config, "architect")

    def compile(self, plan: Dict) -> Dict:
        graph = self.post("/v2/compile", {"plan": plan})
        return validate("work-graph-v1", graph)


class HttpRuntime(HttpService):
    @classmethod
    def from_config(cls, config: Config):
        return super().from_config(config, "runtime")

    def create_workflow(self, *, trace_id: str, plan_id: str, graph_id: str) -> Dict:
        return self.post("/v1/workflows", {
            "trace_id": trace_id,
            "plan_id": plan_id,
            "graph_id": graph_id,
        })

    def transition(self, run_id: str, target: str, *, event_type: str = "matrix_os_transition",
                   payload: Dict | None = None, checkpoint: str = "") -> Dict:
        return self.post(f"/v1/workflows/{run_id}/transition", {
            "target": target,
            "checkpoint": checkpoint,
            "event_type": event_type,
            "payload": payload or {},
        })


class HttpHiveDriver(HttpService):
    @classmethod
    def from_config(cls, config: Config):
        return super().from_config(config, "hive")

    def submit(self, *, work_graph: Dict, policy_grant: Dict, budget_grant: Dict,
               trace: Dict | None = None, workspace: Dict | None = None,
               tenant: Dict | None = None) -> Dict:
        # Hive's internal model does not consume Matrix OS extension fields.
        pg = {
            "grant_id": policy_grant["grant_id"],
            "allowed_capabilities": policy_grant.get("allowed_capabilities", []),
            "forbidden_capabilities": [],
            "expires_at": policy_grant.get("expires_at", ""),
        }
        limits = budget_grant.get("limits") or {}
        bg = {
            "grant_id": budget_grant["grant_id"],
            "max_mxu": budget_grant["max_mxu"],
            "max_tokens": budget_grant.get("max_tokens"),
            "max_tool_calls": limits.get("max_tool_calls"),
            "hard_stop": budget_grant.get("hard_stop", True),
        }
        return self.post("/v2/runs", {
            "work_graph": work_graph,
            "policy_grant": pg,
            "budget_grant": bg,
            "trace": trace or {},
            "workspace": workspace or {},
            "tenant": tenant or {},
        })

    def status(self, run_id: str) -> Dict:
        return self.get(f"/runs/{run_id}")

    def artifacts(self, run_id: str) -> Dict:
        # get_json is object-typed historically; callers accept list payloads from service.
        return self.get(f"/runs/{run_id}/artifacts")

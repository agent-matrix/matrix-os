"""GitPilot adapter — the default, integrated AI coder for Matrix OS.

GitPilot (``ruslanmv/gitpilot``) is *the* code writer in the Agent-Matrix loop.
Code generation has exactly one path: the coder provider, which defaults to
``gitpilot`` and is never bypassed or replaced. New coding capability is added
*inside* GitPilot (more OllaBridge model aliases, more MatrixLab profiles), not
by swapping it out.

The integration boundary is HTTP:

    POST {GITPILOT_URL}/repair   <- a RepairPlan          -> a RepairResponse
    GET  {GITPILOT_URL}/health   availability probe

GitPilot's repair flow (its ``repair/service.py``) runs 12 steps: receive,
clone, branch ``gitpilot/<task_id>``, refuse forbidden/empty allowed_paths
(fail-closed), inspect with ``code-fast``, generate a unified diff with
``code-coder`` (constrained to ``allowed_paths``), apply (only when not dry-run),
review with ``code-reviewer``, sandbox-validate via MatrixLab
``/repo/validate-patch``, assess risk, then branch on mode (draft_pr | dry_run).

Model access: GitPilot reaches models **only through OllaBridge** via
``OPENAI_BASE_URL`` + ``OPENAI_API_KEY`` (an ``ob_*`` gateway key). It never
reads ``HF_TOKEN`` — only OllaBridge holds that.

The HTTP client below is **live**: ``health()`` and ``repair()`` call the real
endpoints and validate the response against the ``repair-response`` contract.
What is *not* yet wired is the kernel's main ``run`` loop — it still uses the
local executor and never calls a coder automatically. Driving the gated loop
through GitPilot (govern -> grant -> coder -> verify) is Batch 4. So a normal
``matrix-os run`` makes no network calls; GitPilot is reached only via the
explicit ``matrix-os coder ...`` commands or a direct ``GitPilotCoder`` call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..config import Config
from ..contracts import validate
from ..http_client import get_json, post_json

# Live GitPilot Space; overridable via MATRIX_GITPILOT_URL.
DEFAULT_GITPILOT_URL = "https://ruslanmv-gitpilot.hf.space"

# OllaBridge model aliases (overridable via GITPILOT_MODEL_FAST/CODER/REVIEWER).
MODEL_FAST = "code-fast"
MODEL_CODER = "code-coder"
MODEL_REVIEWER = "code-reviewer"

# Default fail-closed forbidden paths: never touch secrets/tokens.
DEFAULT_FORBIDDEN_PATHS = [".env", "secrets/**", "**/*token*", "**/*secret*"]


@dataclass
class GitPilotCoder:
    """The default :class:`~matrix_os.adapters.base.CoderPort` implementation."""

    base_url: str = DEFAULT_GITPILOT_URL
    provider: str = "gitpilot"
    coder_model: str = MODEL_CODER
    # Dry-run by default: GitPilot "Plan"/dry_run mode writes nothing.
    default_mode: str = "dry_run"
    timeout: float = 60.0
    retries: int = 2

    @classmethod
    def from_config(cls, config: Config) -> "GitPilotCoder":
        url = config.services.get("gitpilot", DEFAULT_GITPILOT_URL)
        return cls(base_url=url.rstrip("/"))

    # -- contract construction ---------------------------------------------
    def build_repair_plan(
        self,
        *,
        task_id: str,
        repo_url: str,
        allowed_paths: List[str],
        mode: str | None = None,
        issues: List[Dict] | None = None,
        forbidden_paths: List[str] | None = None,
        sandbox_profile: str | None = None,
        client_id: str = "matrix-os",
    ) -> Dict:
        """Assemble a contract-valid RepairPlan (coder.provider defaults to gitpilot)."""
        plan = {
            "client_id": client_id,
            "task_id": task_id,
            "repo_url": repo_url,
            "branch": "main",
            "mode": mode or self.default_mode,
            "issues": issues or [],
            "allowed_paths": allowed_paths,
            "forbidden_paths": forbidden_paths or list(DEFAULT_FORBIDDEN_PATHS),
            "coder": {"provider": self.provider, "model": self.coder_model},
            "sandbox": {
                "provider": "matrixlab",
                "profile": sandbox_profile or "python-repair",
                "required": True,
            },
        }
        return validate("repair-plan", plan)

    # -- live HTTP boundary -------------------------------------------------
    def health(self) -> Dict:
        """GET {base}/health. Raises ServiceError if GitPilot is unreachable."""
        return get_json(f"{self.base_url}/health", timeout=self.timeout)

    def reachable(self) -> bool:
        from ..http_client import ServiceError

        try:
            self.health()
            return True
        except ServiceError:
            return False

    def repair(self, repair_plan: Dict) -> Dict:
        """POST a RepairPlan to {base}/repair; validate and return the RepairResponse."""
        validate("repair-plan", repair_plan)
        resp = post_json(
            f"{self.base_url}/repair",
            repair_plan,
            timeout=self.timeout,
            retries=self.retries,
        )
        return validate("repair-response", resp)

    # -- CoderPort surface --------------------------------------------------
    def plan(self, task: str, repo: str, *, context: Dict | None = None) -> Dict:
        """Read-only dry-run: build the plan, then delegate to /repair (Plan mode)."""
        rp = self.build_repair_plan(
            task_id=task, repo_url=repo, allowed_paths=[], mode="dry_run"
        )
        return self.repair(rp)

    def apply(self, task: str, repo: str, *, dry_run: bool = True) -> Dict:
        """Apply an approved change. ``dry_run`` keeps GitPilot in preview-only mode."""
        rp = self.build_repair_plan(
            task_id=task,
            repo_url=repo,
            allowed_paths=[],
            mode="dry_run" if dry_run else "apply",
        )
        return self.repair(rp)

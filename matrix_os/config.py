"""Runtime configuration for the kernel.

Configuration is read from the process environment (optionally seeded from a
``.env`` file). Safety-relevant switches default to the *secure* value so that
the kernel fails closed when nothing is configured.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from .util import repo_root


def _load_dotenv(path: Path) -> Dict[str, str]:
    """Parse a minimal ``KEY=value`` ``.env`` file. Missing file -> empty dict."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()
    return values


def _as_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


# Service endpoints the kernel may talk to once HTTP adapters land (Batch 2).
SERVICE_ENV_KEYS = {
    "hub": "MATRIX_HUB_URL",
    "context": "MATRIX_CONTEXT_URL",
    "ai": "MATRIX_AI_URL",
    "guardian": "MATRIX_GUARDIAN_URL",
    "architect": "MATRIX_ARCHITECT_URL",
    "treasury": "MATRIX_TREASURY_URL",
    "matrixlab": "MATRIXLAB_URL",
    "runtime": "MATRIX_RUNTIME_URL",
    "hive": "MATRIX_HIVE_DRIVER_URL",
    "llm": "MATRIX_LLM_URL",
    # GitPilot is the default AI coder (integrated, not replaced).
    "gitpilot": "MATRIX_GITPILOT_URL",
    # SelfRepair is the control plane that delegates coding work to GitPilot.
    "selfrepair": "MATRIX_SELFREPAIR_URL",
}


@dataclass
class Config:
    """Resolved kernel configuration."""

    safe_mode: bool = True
    hitl_default: bool = True
    autopilot_enabled: bool = False
    allow_production_deploy: bool = False
    allow_self_modification: bool = False
    allow_network_in_sandbox: bool = False
    operator_token: str = "change-me"
    services: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, env: Dict[str, str] | None = None) -> "Config":
        """Build a Config from a ``.env`` file overlaid with the live environment."""
        merged: Dict[str, str] = {}
        merged.update(_load_dotenv(repo_root() / ".env"))
        merged.update(os.environ)
        if env:
            merged.update(env)

        return cls(
            safe_mode=_as_bool(merged.get("MATRIX_SAFE_MODE"), True),
            hitl_default=_as_bool(merged.get("HITL_DEFAULT"), True),
            autopilot_enabled=_as_bool(merged.get("AUTOPILOT_ENABLED"), False),
            allow_production_deploy=_as_bool(merged.get("ALLOW_PRODUCTION_DEPLOY"), False),
            allow_self_modification=_as_bool(merged.get("ALLOW_SELF_MODIFICATION"), False),
            allow_network_in_sandbox=_as_bool(merged.get("ALLOW_NETWORK_IN_SANDBOX"), False),
            operator_token=merged.get("MATRIX_OPERATOR_TOKEN", "change-me"),
            services={
                name: merged[key]
                for name, key in SERVICE_ENV_KEYS.items()
                if merged.get(key)
            },
        )

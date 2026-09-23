"""Contract loading and validation.

Every object that crosses a component boundary is validated against a versioned
JSON Schema. V1 remains available during migration; V2 freezes the global
cognitive-kernel interfaces.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from jsonschema import Draft202012Validator

from .util import repo_root

CONTRACTS = {
    "plan-ir": "plan-ir.schema.json",
    "policy-grant": "policy-grant.schema.json",
    "budget-grant": "budget-grant.schema.json",
    "evidence-bundle": "evidence-bundle.schema.json",
    "memory-event": "memory-event.schema.json",
    "agent-card": "agent-card.schema.json",
    "repair-plan": "repair-plan.schema.json",
    "repair-response": "repair-response.schema.json",
    "eval-report": "eval-report.schema.json",
    "run-envelope-v2": "run-envelope-v2.schema.json",
    "plan-ir-v2": "plan-ir-v2.schema.json",
    "evidence-bundle-v2": "evidence-bundle-v2.schema.json",
}


class ContractError(ValueError):
    """Raised when an object does not satisfy its contract schema."""


def contracts_dir() -> Path:
    return repo_root() / "contracts"


@lru_cache(maxsize=None)
def _validator(name: str) -> Draft202012Validator:
    if name not in CONTRACTS:
        raise KeyError(f"unknown contract: {name!r}")
    schema = json.loads((contracts_dir() / CONTRACTS[name]).read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate(name: str, obj: Dict) -> Dict:
    errors = sorted(_validator(name).iter_errors(obj), key=lambda e: e.path)
    if errors:
        details = "; ".join(
            f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
            for e in errors
        )
        raise ContractError(f"{name} contract violation: {details}")
    return obj


def load_all_schemas() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for name, fname in CONTRACTS.items():
        schema = json.loads((contracts_dir() / fname).read_text())
        Draft202012Validator.check_schema(schema)
        out[name] = schema
    return out

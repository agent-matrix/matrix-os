import pytest

from matrix_os.contracts import ContractError, load_all_schemas, validate


def test_all_schemas_load_and_self_check():
    schemas = load_all_schemas()
    assert set(schemas) >= {
        "plan-ir",
        "policy-grant",
        "budget-grant",
        "evidence-bundle",
        "memory-event",
        "agent-card",
    }


def test_valid_plan_passes():
    plan = {
        "plan_id": "plan_1",
        "goal": "read the repo",
        "risk": "low",
        "steps": [
            {"id": "s1", "action": "read", "required_capabilities": ["read.repo"]}
        ],
        "verification": {"required": True},
    }
    assert validate("plan-ir", plan) is plan


def test_invalid_plan_rejected():
    with pytest.raises(ContractError):
        validate("plan-ir", {"plan_id": "x", "goal": "g"})  # missing risk/steps


def test_invalid_enum_rejected():
    with pytest.raises(ContractError):
        validate(
            "policy-grant",
            {"grant_id": "g", "plan_id": "p", "decision": "maybe"},
        )

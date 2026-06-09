from matrix_os.policy import PolicyEngine


def _plan(risk, caps, action="do thing"):
    return {
        "plan_id": "plan_x",
        "goal": "g",
        "risk": risk,
        "steps": [
            {"id": "s1", "action": action, "required_capabilities": caps}
        ],
        "verification": {},
    }


def test_low_risk_allows():
    d = PolicyEngine().evaluate(_plan("low", ["read.repo"]))
    assert d.decision == "allow"
    assert "read.repo" in d.allowed_capabilities


def test_medium_capability_requires_sandbox():
    d = PolicyEngine().evaluate(_plan("low", ["fs.apply_patch"]))
    assert d.effective_risk == "medium"
    assert d.decision == "require_sandbox"


def test_critical_capability_denies():
    d = PolicyEngine().evaluate(_plan("low", ["deploy.production"]))
    assert d.effective_risk == "critical"
    assert d.decision == "deny"
    assert d.allowed_capabilities == []


def test_unknown_capability_is_high_risk():
    d = PolicyEngine().evaluate(_plan("low", ["mystery.capability"]))
    assert d.effective_risk == "high"
    assert d.decision == "require_human_approval"


def test_denylisted_command_triggers_emergency_stop():
    d = PolicyEngine().evaluate(_plan("low", ["shell.run"], action="rm -rf / now"))
    assert d.decision == "emergency_stop"
    assert d.blocked


def test_high_risk_plan_needs_human():
    d = PolicyEngine().evaluate(_plan("high", ["read.repo"]))
    assert d.decision == "require_human_approval"
    assert d.needs_human

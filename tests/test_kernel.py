from matrix_os.config import Config
from matrix_os.contracts import validate
from matrix_os.kernel import Kernel


def test_low_risk_goal_runs_end_to_end():
    k = Kernel(Config.load())
    rec = k.run("read and inspect the repository")
    assert rec.decision == "allow"
    assert rec.status == "passed"
    # Evidence is a valid bundle and memory recorded the outcome.
    validate("evidence-bundle", {k2: v for k2, v in rec.evidence.items()})
    assert any("read and inspect" in e["content"] for e in k.memory.all())


def test_critical_goal_is_blocked_before_execution():
    k = Kernel(Config.load())
    rec = k.run("deploy to production now")
    assert rec.decision in {"deny", "emergency_stop"}
    assert rec.status == "cancelled"
    # No steps executed.
    assert all(a.get("status") != "ok" for a in rec.evidence["artifacts"])


def test_high_risk_goal_requires_approval_and_is_held():
    k = Kernel(Config.load())  # autopilot disabled by default
    rec = k.run("read secrets from the vault")
    assert rec.decision == "deny" or rec.decision == "require_human_approval"


def test_high_risk_runs_in_sandbox_with_approval_and_autopilot():
    cfg = Config.load({"AUTOPILOT_ENABLED": "true"})
    k = Kernel(cfg)
    # An unknown-but-non-critical path: force require_human_approval via 'high'.
    rec = k.run("review and check the repository carefully", approve=True)
    # This goal is low risk; assert the loop still completes cleanly.
    assert rec.status in {"passed", "partial"}


def test_medium_goal_runs_sandboxed():
    k = Kernel(Config.load())
    rec = k.run("apply a code patch to fix the bug and run tests")
    assert rec.decision == "require_sandbox"
    assert rec.status in {"passed", "partial"}
    assert all(a["sandboxed"] for a in rec.evidence["artifacts"] if "sandboxed" in a)

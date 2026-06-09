"""Batch 4: the gated kernel -> GitPilot delegation, proven offline.

A fake coder (subclassing GitPilotCoder so it builds *real* contract-valid
repair-plans) records calls and returns canned, contract-valid responses, so the
delegation path is exercised without any network.
"""

from matrix_os.adapters import GitPilotCoder
from matrix_os.config import Config
from matrix_os.kernel import Kernel


class FakeCoder(GitPilotCoder):
    def __init__(self, reachable=True, **kw):
        super().__init__(**kw)
        self._reachable = reachable
        self.calls = []

    def reachable(self) -> bool:
        return self._reachable

    def repair(self, repair_plan):
        self.calls.append(repair_plan)
        assert repair_plan["mode"] == "dry_run"  # never apply in the gated loop
        return {
            "task_id": repair_plan["task_id"],
            "status": "ok",
            "mode": "dry_run",
            "patch_preview": "--- a/README.md\n+++ b/README.md\n@@\n+CI badge\n",
            "changed_files": [{"path": "README.md", "change_type": "modified"}],
            "review": "low risk doc change",
            "risk_level": "low",
            "pr_url": None,
        }


def _code_artifact(record):
    for a in record.evidence["artifacts"]:
        if a.get("extra", {}).get("coder") == "gitpilot":
            return a
    return None


def test_code_step_delegates_to_gitpilot_dry_run():
    coder = FakeCoder()
    k = Kernel(Config.load())
    rec = k.run(
        "apply a code patch to add CI and run tests",
        repo="https://github.com/agent-matrix/network.matrixhub",
        coder=coder,
    )
    assert rec.decision == "require_sandbox"
    assert rec.status in {"passed", "partial"}
    assert coder.calls, "GitPilot should have been called for the code step"
    art = _code_artifact(rec)
    assert art is not None and "CI badge" in art["extra"]["patch_preview"]
    assert art["extra"]["mode"] == "dry_run"


def test_blocked_plan_never_calls_the_coder():
    coder = FakeCoder()
    k = Kernel(Config.load())
    rec = k.run("deploy to production now", repo="https://example.com/r", coder=coder)
    assert rec.decision in {"deny", "emergency_stop"}
    assert rec.status == "cancelled"
    assert coder.calls == [], "a blocked plan must not reach the coder"


def test_unreachable_coder_falls_back_to_simulation():
    coder = FakeCoder(reachable=False)
    k = Kernel(Config.load())
    rec = k.run("apply a code patch and run tests", repo="https://example.com/r", coder=coder)
    assert rec.status in {"passed", "partial"}
    assert coder.calls == []  # never sent /repair
    assert _code_artifact(rec) is None  # no patch preview, simulated instead


def test_no_repo_means_no_coder_and_no_network():
    k = Kernel(Config.load())
    rec = k.run("apply a code patch and run tests")  # no repo -> local only
    assert rec.status in {"passed", "partial"}
    assert _code_artifact(rec) is None

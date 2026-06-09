from matrix_os.adapters import CoderPort, GitPilotCoder
from matrix_os.config import Config
from matrix_os.contracts import validate


def test_gitpilot_is_the_default_coder():
    c = GitPilotCoder.from_config(Config.load())
    assert c.provider == "gitpilot"
    assert c.default_mode == "dry_run"  # dry-run first
    assert isinstance(c, CoderPort)


def test_repair_plan_is_contract_valid_and_fail_closed_defaults():
    c = GitPilotCoder()
    rp = c.build_repair_plan(
        task_id="t1",
        repo_url="https://github.com/agent-matrix/network.matrixhub",
        allowed_paths=["tests/**", "README.md"],
        issues=[{"id": "i1", "severity": "medium", "description": "missing CI"}],
    )
    validate("repair-plan", rp)
    assert rp["coder"]["provider"] == "gitpilot"
    assert rp["mode"] == "dry_run"
    # Secrets are never writable by default.
    assert ".env" in rp["forbidden_paths"]
    assert rp["sandbox"]["provider"] == "matrixlab"


def test_repair_response_contract():
    resp = {
        "task_id": "t1",
        "status": "ok",
        "mode": "dry_run",
        "patch_preview": "--- a\n+++ b\n",
        "changed_files": [{"path": "README.md", "change_type": "modified"}],
        "risk_level": "low",
        "pr_url": None,
    }
    validate("repair-response", resp)

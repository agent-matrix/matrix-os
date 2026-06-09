import json

from matrix_os.config import Config
from matrix_os.dashboard import build_dashboard, write_dashboard
from matrix_os.kernel import Kernel


def test_dashboard_reflects_real_runs():
    k = Kernel(Config.load())
    k.run("read and inspect the repository")  # allow / passed
    k.run("deploy to production")             # deny / cancelled

    d = build_dashboard()
    labels = {m["label"]: m["value"] for m in d["metrics"]}
    assert "Total Runs" in labels
    assert "Governance Health" in labels
    # metric icons are JSON-safe string keys the frontend resolves via O[...]
    assert all(isinstance(m["ic"], str) for m in d["metrics"])
    # workflows/events carry the real goals
    flat = json.dumps(d)
    assert "deploy to production" in flat
    assert d["coder_task"]["mode"] == "dry_run"
    assert d["coder_task"]["coder"].startswith("GitPilot")


def test_write_dashboard_emits_valid_json(tmp_path):
    out = write_dashboard(tmp_path / "data.json")
    parsed = json.loads(out.read_text())
    assert "metrics" in parsed and len(parsed["metrics"]) == 4

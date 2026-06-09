"""Prove the live HTTP coder boundary against a local stub GitPilot server.

No external network: a threaded http.server speaks GitPilot's /health and
/repair so the round-trip and contract validation are exercised offline.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from matrix_os.adapters import GitPilotCoder
from matrix_os.http_client import ServiceError, get_json


class _StubGitPilot(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence test output
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "gitpilot"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        plan = json.loads(self.rfile.read(length) or "{}")
        # Echo a contract-valid repair-response in dry-run mode.
        self._send(200, {
            "task_id": plan.get("task_id", "?"),
            "status": "ok",
            "mode": plan.get("mode", "dry_run"),
            "patch_preview": "--- a/README.md\n+++ b/README.md\n@@\n+CI added\n",
            "changed_files": [{"path": "README.md", "change_type": "modified"}],
            "review": "looks good, low risk",
            "risk_level": "low",
            "pr_url": None,
        })


@pytest.fixture
def stub_server():
    server = HTTPServer(("127.0.0.1", 0), _StubGitPilot)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}"
    server.shutdown()


def test_health_roundtrip(stub_server):
    coder = GitPilotCoder(base_url=stub_server)
    assert coder.health()["status"] == "ok"
    assert coder.reachable() is True


def test_repair_roundtrip_validates_contract(stub_server):
    coder = GitPilotCoder(base_url=stub_server)
    plan = coder.build_repair_plan(
        task_id="t42",
        repo_url="https://github.com/agent-matrix/network.matrixhub",
        allowed_paths=["README.md", ".github/**"],
        mode="dry_run",
    )
    resp = coder.repair(plan)  # validates repair-response on the way out
    assert resp["status"] == "ok"
    assert resp["task_id"] == "t42"
    assert resp["changed_files"][0]["path"] == "README.md"
    assert "CI added" in resp["patch_preview"]


def test_unreachable_raises_service_error():
    # Port 1 is not listening; expect a clean ServiceError, not a raw traceback.
    with pytest.raises(ServiceError):
        get_json("http://127.0.0.1:1/health", timeout=1.0)
    assert GitPilotCoder(base_url="http://127.0.0.1:1").reachable() is False

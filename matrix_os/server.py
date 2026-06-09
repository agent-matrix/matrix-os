"""Matrix OS server: the backend API + the static console, served together.

A dependency-free (stdlib) HTTP server that serves the ``frontend/`` console and
exposes the kernel over a small JSON API on the same origin, so the console gets
**live** data with no build step and no CORS:

    GET  /                 -> the Admin Command Center (frontend/index.html)
    GET  /data.json        -> live dashboard snapshot (regenerated per request)
    GET  /api/health       -> {"status": "ok"}
    GET  /api/metrics      -> run metrics
    GET  /api/dashboard    -> same as /data.json
    POST /api/run {goal}   -> run the governed loop, return the run record

If the requested port is busy the server walks up to the next free port.
"""

from __future__ import annotations

import functools
import json
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple

from .util import repo_root


def find_free_port(start: int = 8080, host: str = "127.0.0.1", tries: int = 64) -> int:
    """Return the first free port at or above ``start`` (scans ``tries`` ports)."""
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"no free port found in {start}..{start + tries}")


class MatrixOSHandler(SimpleHTTPRequestHandler):
    """Serves the static console plus the live JSON API."""

    def log_message(self, fmt, *args):  # keep the console quiet
        return

    def _json(self, obj, code: int = 200):
        body = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        if route in ("/data.json", "/api/dashboard"):
            from .dashboard import build_dashboard
            return self._json(build_dashboard())
        if route == "/api/metrics":
            from .metrics import compute, load_runs
            return self._json(compute(load_runs()))
        if route == "/api/health":
            return self._json({"status": "ok", "service": "matrix-os"})
        return super().do_GET()

    def do_POST(self):
        route = self.path.split("?", 1)[0]
        if route == "/api/run":
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                payload = json.loads(self.rfile.read(length) or "{}")
            except ValueError:
                return self._json({"error": "invalid json"}, 400)
            goal = (payload.get("goal") or "").strip()
            if not goal:
                return self._json({"error": "missing 'goal'"}, 400)
            from .config import Config
            from .kernel import Kernel
            rec = Kernel(Config.load()).run(goal, approve=bool(payload.get("approve")))
            return self._json({
                "run_id": rec.run_id, "goal": rec.goal, "decision": rec.decision,
                "status": rec.status, "reasons": rec.reasons,
                "evidence_id": rec.evidence["evidence_id"],
            })
        return self._json({"error": "not found"}, 404)


def make_server(
    host: str = "127.0.0.1", port: int = 8080, directory: Path | None = None
) -> Tuple[ThreadingHTTPServer, int]:
    """Build a server bound to the first free port at or above ``port``."""
    directory = directory or (repo_root() / "frontend")
    actual = find_free_port(port, host)
    handler = functools.partial(MatrixOSHandler, directory=str(directory))
    httpd = ThreadingHTTPServer((host, actual), handler)
    return httpd, actual


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run the backend + console until interrupted."""
    httpd, actual = make_server(host, port)
    note = "" if actual == port else f"  (port {port} busy → {actual})"
    print(f"Matrix OS  ·  console + API  →  http://{host}:{actual}{note}")
    print("  GET / · /data.json · /api/health · /api/metrics    POST /api/run {goal}")
    print("Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        httpd.shutdown()
        httpd.server_close()

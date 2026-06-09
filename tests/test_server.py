import json
import socket
import threading
import urllib.request

from matrix_os.server import find_free_port, make_server


def _get(url):
    with urllib.request.urlopen(url, timeout=3) as r:
        return r.status, json.loads(r.read().decode())


def test_find_free_port_skips_busy_ports():
    # Hold a port, then assert the finder walks past it.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", 0))
        busy = s.getsockname()[1]
        s.listen(1)
        nxt = find_free_port(busy, "127.0.0.1")
        assert nxt > busy


def test_server_serves_live_api():
    httpd, port = make_server("127.0.0.1", find_free_port(8390))
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        code, health = _get(base + "/api/health")
        assert code == 200 and health["status"] == "ok"

        code, data = _get(base + "/data.json")
        assert code == 200 and isinstance(data["metrics"], list)

        # POST /api/run drives the governed loop.
        req = urllib.request.Request(
            base + "/api/run",
            data=json.dumps({"goal": "read and inspect the repository"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            run = json.loads(r.read().decode())
        assert run["decision"] == "allow"
        assert run["status"] == "passed"
    finally:
        httpd.shutdown()
        httpd.server_close()

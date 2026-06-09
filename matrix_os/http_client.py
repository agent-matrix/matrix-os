"""Tiny JSON-over-HTTP client (stdlib only).

Used by the live service adapters. Kept dependency-free (``urllib``) so the
kernel installs with nothing heavier than ``jsonschema`` + ``PyYAML``. Provides
timeouts and bounded exponential-backoff retries, and normalises every transport
failure into :class:`ServiceError`.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Dict, Optional


class ServiceError(RuntimeError):
    """A service call failed (transport error, timeout, or bad HTTP status)."""


def _request(
    method: str,
    url: str,
    payload: Optional[Dict],
    headers: Optional[Dict[str, str]],
    timeout: float,
) -> Dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted URLs)
        body = resp.read().decode("utf-8")
    return json.loads(body) if body.strip() else {}


def get_json(url: str, *, timeout: float = 10.0, headers: Optional[Dict] = None) -> Dict:
    try:
        return _request("GET", url, None, headers, timeout)
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        raise ServiceError(f"GET {url} failed: {exc}") from exc


def post_json(
    url: str,
    payload: Dict,
    *,
    timeout: float = 30.0,
    headers: Optional[Dict] = None,
    retries: int = 2,
    backoff: float = 0.5,
) -> Dict:
    last: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            return _request("POST", url, payload, headers, timeout)
        except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
    raise ServiceError(f"POST {url} failed after {retries + 1} attempts: {last}")

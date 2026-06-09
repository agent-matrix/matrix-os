"""Small shared helpers: ids, timestamps, hashing, repo paths."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def new_id(prefix: str) -> str:
    """Return a short, prefixed, unique id (e.g. ``plan_3f2a1b9c``)."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def utc_now() -> str:
    """ISO-8601 UTC timestamp with a trailing ``Z``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def digest(data: object) -> str:
    """Stable sha256 digest of any JSON-serialisable object."""
    blob = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def repo_root() -> Path:
    """Locate the Matrix OS home (where ``contracts/`` and ``policies/`` live).

    Order of precedence:
      1. ``MATRIX_OS_HOME`` environment variable.
      2. The repository checkout that contains this package.
    """
    env = os.environ.get("MATRIX_OS_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def state_dir() -> Path:
    """Local working directory for logs, evidence, and memory (``.matrix/``)."""
    d = repo_root() / ".matrix"
    return d

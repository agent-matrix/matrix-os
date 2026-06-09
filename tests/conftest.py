"""Test fixtures: isolate kernel state under a temp directory."""

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Point MATRIX_OS_HOME at a temp copy of contracts/ + policies/.

    This keeps the real ``.matrix/`` working directory clean and lets tests run
    hermetically while still exercising the real schemas and policies.
    """
    for sub in ("contracts", "policies", "evals"):
        dst = tmp_path / sub
        dst.mkdir()
        for f in (REPO_ROOT / sub).glob("*"):
            if f.is_file():
                (dst / f.name).write_bytes(f.read_bytes())
    monkeypatch.setenv("MATRIX_OS_HOME", str(tmp_path))

    # Reset cached loaders that captured the old root.
    from matrix_os import contracts, policy

    contracts._validator.cache_clear()
    policy._load.cache_clear()
    yield

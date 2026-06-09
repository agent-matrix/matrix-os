"""The memory and context plane (local file-backed v0.1).

Memory events follow ``contracts/memory-event.schema.json``. This first version
stores events as JSONL under ``.matrix/memory/events.jsonl`` and offers naive
keyword retrieval. Batch 3 will swap this for the Matrix Context service behind
the same interface without changing the kernel.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .contracts import validate
from .util import new_id, state_dir, utc_now


class MemoryStore:
    """Append-only, inspectable memory. No agent acts on un-inspectable context."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (state_dir() / "memory" / "events.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        *,
        type: str,
        scope: str,
        content: str,
        source: str,
    ) -> Dict:
        """Validate and append a memory event. Returns the stored event."""
        event = {
            "event_id": new_id("mem"),
            "type": type,
            "scope": scope,
            "content": content,
            "source": source,
            "timestamp": utc_now(),
        }
        validate("memory-event", event)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")
        return event

    def all(self) -> List[Dict]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text().splitlines()
            if line.strip()
        ]

    def retrieve(
        self,
        query: str,
        *,
        type: str | None = None,
        scope: str | None = None,
        limit: int = 5,
    ) -> List[Dict]:
        """Return up to ``limit`` events ranked by keyword overlap with ``query``.

        Optionally filter by memory ``type`` (semantic/episodic/procedural/...)
        and/or ``scope``. Ties (including the empty-overlap case) fall back to
        recency, so a fresh store still returns the most recent context.
        """
        events = self.all()
        if type is not None:
            events = [e for e in events if e.get("type") == type]
        if scope is not None:
            events = [e for e in events if e.get("scope") == scope]
        terms = {t for t in query.lower().split() if len(t) > 2}

        def score(ev: Dict) -> int:
            words = set(ev.get("content", "").lower().split())
            return len(terms & words)

        ranked = sorted(
            enumerate(events),
            key=lambda pair: (score(pair[1]), pair[0]),
            reverse=True,
        )
        return [ev for _, ev in ranked[:limit]]

    # -- learning -----------------------------------------------------------
    def learn_from_run(self, record) -> List[Dict]:
        """Consolidate one run's outcome into memory.

        Always records an episodic trace. Derives a *procedural* lesson when a
        run is blocked or fails (so future similar goals can be steered), and a
        *semantic* fact when it succeeds. This is the kernel's ``learn`` stage.
        """
        goal = record.goal
        decision = record.decision
        status = record.status
        risk = record.plan.get("risk")
        nsteps = len(record.evidence.get("artifacts", []))
        written: List[Dict] = []

        written.append(self.write(
            type="episodic",
            scope="run",
            content=f"goal '{goal}' -> {decision}/{status} ({nsteps} artifacts)",
            source=f"kernel/{record.run_id}",
        ))

        if decision in {"deny", "emergency_stop"} or status == "failed":
            written.append(self.write(
                type="procedural",
                scope="policy",
                content=(
                    f"AVOID: goals like '{goal}' were {decision} at risk {risk}; "
                    f"seek a lower-risk framing or explicit human approval"
                ),
                source=f"kernel/{record.run_id}",
            ))
        elif status == "passed":
            written.append(self.write(
                type="semantic",
                scope="capability",
                content=f"SUCCESS: '{goal}' completed at risk {risk} via {nsteps} steps",
                source=f"kernel/{record.run_id}",
            ))

        return written

# ADR 0001: GitPilot is the default AI coder (integrate, do not replace)

- Status: accepted
- Date: 2026-06-08

## Context

Matrix OS orchestrates a governed-autonomy loop but does **not** write code
itself. Several Agent-Matrix components can execute work (Matrix Architect,
Matrix Runtime, MatrixLab, Matrix Maintainer), and it would be tempting to grow
a bespoke code writer inside the kernel. The ecosystem already has a dedicated,
purpose-built AI coder — **GitPilot** (`ruslanmv/gitpilot`) — a multi-agent
assistant (Explorer / Planner / Coder / Reviewer) with safe execution modes.

## Decision

**GitPilot is the default AI coder for Matrix OS. It is integrated, never
replaced.** Any code-writing capability (e.g. `fs.apply_patch`) is delegated to
GitPilot through the `CoderPort` seam (`matrix_os/adapters/base.py`), with the
default implementation `GitPilotCoder` (`matrix_os/adapters/gitpilot.py`).

Roles stay separated (the ecosystem "golden rules"):

- **GitPilot** — generic AI coder. Writes patches. **Dry-run first** (its "Plan"
  mode is read-only and is the default-safe path).
- **SelfRepair** — control plane / system of record. Diagnoses, plans, delegates
  coding to GitPilot, validates via MatrixLab, reports. Does not write code.
- **MatrixLab** — sandbox verification provider for whatever GitPilot produces.
- **Matrix OS** — orchestrates the loop and enforces the govern → execute gate.
  It routes coding work to GitPilot; it does not reimplement a coder.

## Mode mapping

| GitPilot mode | Matrix OS meaning |
|---|---|
| Plan (default) | read-only dry-run — produce a diff, write nothing |
| Ask | approval-gated — pairs with Guardian `require_human_approval` |
| Auto | unattended — only under an explicit policy + budget grant |

GitPilot HTTP surface used by the integration: `POST /api/chat/plan`,
`POST /api/chat/execute`, `POST /api/v2/chat/stream` (`permission_mode`),
`POST /api/v2/approval/respond`, `PUT /api/permissions/mode`. Live Space:
`https://ruslanmv-gitpilot.hf.space` (override via `MATRIX_GITPILOT_URL`).

## Consequences

- The kernel's `CoderPort` defaults to `GitPilotCoder`; alternative coders are
  opt-in, not the default.
- The live wiring lands in **Batch 4** (AI-coder PR workflow via SelfRepair).
  Until then `GitPilotCoder` is inert (no network calls) and the local executor
  is used, so no real patches are written without the gate in place.
- Secrets discipline is preserved: model credentials live in the gateway
  (OllaBridge), not in Matrix OS or GitPilot config carried by the kernel.

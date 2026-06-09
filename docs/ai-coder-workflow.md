# AI Coder Workflow — GitPilot as the integrated, default coder

This is the canonical description of the repair-and-coder loop. **GitPilot is the
one and only code writer in the flow**, wired as the default provider — never
bypassed, never replaced. The coder-provider abstraction exists so another coder
*could* be added later, but new capability is added *inside* GitPilot (more
OllaBridge model aliases, more MatrixLab profiles), not by swapping it out.

## 1. The cast

| Component | Role in the loop |
|---|---|
| **OllaBridge Cloud** | Inference gateway. Serves models behind aliases (`code-fast`, `code-coder`, `code-reviewer`, `repo-planner`, `risk-classifier`) over OpenAI-compatible `/v1/chat/completions`. **Only holder of `HF_TOKEN`.** |
| **SelfRepair** | Control plane / system of record. Diagnoses repos, builds a repair-plan, **delegates code-writing to GitPilot**, asks MatrixLab to validate, reports. *Never writes code itself.* |
| **GitPilot** | **The AI coder.** Turns a repair-plan into a unified-diff patch, reviews it, sandbox-validates, optionally opens a draft PR. Talks to models **only through OllaBridge**. |
| **MatrixLab** | Sandbox validator. Runs/validates the patched branch in an isolated profile. |
| **matrix-maintainer** | Agent-Matrix "first client." Schedules maintenance and submits requests to SelfRepair's control plane. |

Key principle: **code generation has exactly one path — GitPilot.** SelfRepair
and matrix-maintainer hold a `coder.provider` field that defaults to `gitpilot`;
they call GitPilot, they don't embed their own coder.

## 2. End-to-end workflow

```
 matrix-maintainer (daily cron / matrix-codex)
   │  POST /v1/plans  {repo, mode:dry_run, client_id:matrix-maintainer}
   ▼
 SelfRepair (control plane = system of record)
   │  1) ANALYZE repo  → detectors (missing CI/tests/license/...) → health_score
   │  2) PLAN          → repair-plan.json
   │  3) DELEGATE to the coder provider (DEFAULT = GitPilot)
   ▼
 GitPilot (the coder) ── runs its 12-step repair flow
   │     models via OllaBridge:  code-fast → code-coder → code-reviewer
   │     validation via MatrixLab:  /repo/validate-patch
   ▼  repair-response.json
 SelfRepair
   │  4) RECORD job + notification ("report ready") + build report.json/md/html
   ▼
 matrix-maintainer ── records the run; surfaces it in the console (Inbox/bell)
```

SelfRepair ↔ GitPilot is an HTTP boundary: `POST {GITPILOT_URL}/repair` with the
repair-plan, `GET /health` for availability. If GitPilot is unreachable,
SelfRepair degrades to a stub so a dry-run still completes — but the *real* coder
is always GitPilot.

## 3. Inside GitPilot — the 12-step repair flow (`repair/service.py`)

1. **Receive** the repair request (the repair-plan).
2. **Clone** the repo into a temp workspace (stubbed in dry-run/demo if unreachable).
3. **Create branch** `gitpilot/<task_id>`.
4. **Refuse forbidden paths** up front — *if `allowed_paths` is empty → fail-closed, block immediately.*
5. **Inspect context** with **`code-fast`**.
6. **Generate the patch** with **`code-coder`** — a unified diff, prompt hard-constrained to `allowed_paths`, told never to touch `.env`/secrets/tokens.
7. **Apply the patch** locally *(only when not dry-run and a workspace exists; dry-run is preview-only).*
8. **Review the patch** with **`code-reviewer`** → review + risk read.
9. **Sandbox-validate** via MatrixLab `/repo/validate-patch` (e.g. profile `python-repair`).
10. **Assess risk** (low/medium/high) from review + changed files.
11. **`draft_pr` mode** → open a draft PR via `pr_writer` *(first-wave: stub).*
12. **`dry_run` mode** → return the **patch preview only**, no PR, no push.

The three model calls map 1:1 to OllaBridge aliases (configurable via
`GITPILOT_MODEL_FAST/CODER/REVIEWER`, defaults `code-fast/code-coder/code-reviewer`).
GitPilot's inference client reads **only** `OPENAI_BASE_URL` + `OPENAI_API_KEY`
(the OllaBridge `ob_*` key) — **it never reads `HF_TOKEN`.**

## 4. Contracts and modes

- **In** — `contracts/repair-plan.schema.json` (SelfRepair → GitPilot).
- **Out** — `contracts/repair-response.schema.json` (GitPilot → SelfRepair).

Both are registered in `matrix_os/contracts.py` and validated by
`matrix-os validate`. The `GitPilotCoder` adapter builds contract-valid
repair-plans (`matrix_os/adapters/gitpilot.py`).

**Modes:**

- `dry_run` (default everywhere) → preview only, **no PR, no push** — safe for public/CI.
- `draft_pr` → open a **draft** PR (never auto-merge); first-wave is a stub.
- `apply` → apply to the working branch (gated; not used in the public loop yet).

## 5. Safety & governance (fail-closed)

GitPilot blocks (returns `blocked`/`error`, no changes) if **any** hold:

- `allowed_paths` is empty, or a changed file is **outside** `allowed_paths`, or matches `forbidden_paths`;
- the patch touches `.env` / secrets / tokens;
- `sandbox.required=true` and MatrixLab is unavailable, or sandbox validation fails;
- `risk_level=high` and no human-approval flag.

Global rule: **only OllaBridge holds `HF_TOKEN`**; GitPilot / SelfRepair /
MatrixLab only ever use `ob_*` gateway keys and service URLs.

## 6. Live vs. stubbed today

- **Live/proven:** OllaBridge gateway; GitPilot's full repair flow + `gitpilot repair --dry-run` CLI (real constrained patch preview, review, MatrixLab call, correct fail-close); SelfRepair plan generator + GitPilot client; MatrixLab sandbox; the control-plane loop (matrix-maintainer → SelfRepair → real GitHub-API health check → report).
- **Stubbed / next to wire:** the **draft-PR writer** (no real PR in first wave, by design), and **matrix-maintainer's `GitPilotAgent`** adapter hook to GitPilot's HTTP `/repair`. Turning on real draft PRs = flip `mode:"draft_pr"` + give GitPilot a scoped, least-privilege Git token (never `HF_TOKEN`).

## 7. How Matrix OS maps onto this

The kernel's `CoderPort` (`matrix_os/adapters/base.py`) defaults to
`GitPilotCoder`. A code-writing capability (`fs.apply_patch`) is delegated to
GitPilot via `/repair`; Guardian still gates it and MatrixLab still verifies.
Live wiring lands in **Batch 4**; until then the adapter is inert (no network
calls) and the local executor is used, so no real patches are written.

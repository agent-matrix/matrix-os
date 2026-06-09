# TODO — production wiring (next session)

This file captures the remaining work to take **matrix-os** from the
implemented v0.1 kernel to *production-wired* against the live, bearer-secured
Agent-Matrix self-maintenance ecosystem. Scope here is **matrix-os only** — the
SelfRepair / GitPilot / MatrixLab / OllaBridge / matrix-maintainer changes are
owned outside this repo and tracked under "External prerequisites".

## Context — the live system (from the handoff)

```
matrix-maintainer ──POST /v1/plans (Bearer SELFREPAIR_INGEST_TOKEN, HTTPS)──▶
SelfRepair (control plane: analyze → plan → delegate → record)
   └─POST /repair (Bearer GITPILOT_API_TOKEN, HTTPS, retry on 429)──▶
     GitPilot (default coder, 12-step dry-run: code-fast → code-coder → code-reviewer)
        ├─ models via OllaBridge (owns HF_TOKEN, ob_ keys)
        └─ sandbox via MatrixLab (/repo/validate-patch)
   ◀── repair-response {patch_preview, review, risk, sandbox_result}
```

Proven live: `network.matrixhub` → health 50 → GitPilot returned a real dry-run
patch → attached to the report. Bearer-gated coder API: `401` without token,
`200` with.

## Verified state of matrix-os today

- ✅ Kernel loop, fail-closed policy engine, contracts, evidence, memory, evals — done, 36 tests.
- ✅ `repair-plan` / `repair-response` contracts match the SelfRepair ↔ GitPilot boundary.
- ✅ `GitPilotCoder` calls `GET /health` + `POST /repair` and validates the response.
- ✅ Gated kernel loop delegates `fs.apply_patch` steps to GitPilot in **dry-run**, with safe fallback.
- ⚠️ **Gap:** `GitPilotCoder` sends **no `Authorization` header** → would `401` against the bearer-gated prod GitPilot.
- ⚠️ **Gap:** `Config` has no token fields (`GITPILOT_API_TOKEN`, `SELFREPAIR_INGEST_TOKEN`).
- ⚠️ **Gap:** `http_client.post_json` retries on *any* HTTP error (incl. 401/403) and ignores `Retry-After`.
- ⚠️ **Missing:** no SelfRepair control-plane client (`POST /v1/plans`) — matrix-os cannot yet act as an operator/sender.

## Production wires to complete (matrix-os scope)

- [ ] **1. Bearer auth on the coder client.**
      `matrix_os/adapters/gitpilot.py`: send `Authorization: Bearer <token>` on
      `POST /repair` (health stays public). Add `auth_token` to `GitPilotCoder`,
      sourced from config. `http_client.post_json/get_json` already accept
      `headers=` — thread the header through.
      *Accept:* `matrix-os coder dry-run` against the live Space returns `200`
      with a token and a clear `401` error message without one.

- [ ] **2. Token configuration.**
      `matrix_os/config.py`: add `gitpilot_token` (`GITPILOT_API_TOKEN`) and
      `selfrepair_token` (`SELFREPAIR_INGEST_TOKEN`). Update `.env.example` with
      both (names only) plus the config-gated flags below. Never log token values.

- [ ] **3. Smarter retry/backoff in `http_client`.**
      Distinguish HTTP status: **retry on 429/5xx honoring `Retry-After`**, do
      **not** retry on 401/403/404. Surface the status code on `ServiceError`.
      *Accept:* a 429 stub is retried with the server's delay; a 401 fails fast.

- [ ] **4. SelfRepair control-plane client (operator path).**
      New `matrix_os/adapters/selfrepair.py`: `submit_plan(repo, mode="dry_run")`
      → `POST {SELFREPAIR_URL}/v1/plans` with `Bearer SELFREPAIR_INGEST_TOKEN`,
      `client_id` configurable. Optional CLI: `matrix-os maintain <repo>`.
      Keep dry-run default; this lets matrix-os drive the same loop the
      matrix-maintainer cron does. *(Optional — only if matrix-os should act as a sender.)*

- [ ] **5. Live integration smoke (opt-in, CI stays offline).**
      `tests/test_live.py` guarded by `MATRIX_OS_LIVE=1` + a token env var;
      skipped by default. Hits `/api/health` and a dry-run `/repair`.
      *Accept:* `make test` stays fully offline; `MATRIX_OS_LIVE=1 make test` exercises prod.

- [ ] **6. End-to-end `matrix-os run --repo` against live GitPilot.**
      With token configured, confirm a code-step run delegates to the live coder,
      attaches the real `patch_preview` to the evidence bundle, and stays dry-run.

- [ ] **7. Docs.**
      Update `docs/ai-coder-workflow.md` and `docs/adr/0001-gitpilot-default-coder.md`
      to note bearer auth on `/repair`, the `429`/`Retry-After` policy, and the
      config-gated flags. Add a short "Production" section to the README.

## External prerequisites (owned outside matrix-os — do not edit here)

One flag each, set by the owner on the respective Space/repo:

- [ ] **Real model patches:** `GITPILOT_CODER_DEMO=false` on the GitPilot Space (currently deterministic demo stub).
- [ ] **Reliable daily analysis:** read-only `GITHUB_TOKEN` on the SelfRepair Space (avoids GitHub rate limits).
- [ ] **Automatic daily runs:** `SELFREPAIR_BASE_URL` + `SELFREPAIR_INGEST_TOKEN` secrets on the matrix-maintainer repo (cron already committed).

## Safety invariants to preserve (do not regress)

- Dry-run by default · no real PRs from matrix-os · fail-closed on allowed/forbidden paths.
- Only OllaBridge holds `HF_TOKEN`; matrix-os carries **only** service URLs + `ob_`/bearer service tokens.
- Tokens never logged, never written to evidence bundles, never committed.
- HTTPS only for machine paths; bearer on every machine endpoint (`/repair`, `/v1/plans`).
- `make test` must remain fully offline; all live checks are opt-in behind an env flag.

## Definition of done

`MATRIX_OS_LIVE=1` + tokens configured → `matrix-os run "<goal>" --repo <url>`
produces a real GitPilot dry-run patch preview in the evidence bundle, the coder
API authenticates (`200`), retries behave (429 honored / 401 fast-fails), and the
default `make test` / `make evals` remain green and offline.

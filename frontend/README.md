# Matrix OS — Admin Command Center (frontend)

The simplest usable frontend for Matrix OS: a single-page **Admin Command Center**
implementing the `MatrixOS.html` design (Matrix-film phosphor green on black,
cinematic digital rain, live topology). It is a static bundle — no build step —
that reads live data from this matrix-os kernel.

## Files

| File | Purpose |
|---|---|
| `index.html` | Entry point: fonts, canvas digital rain, React + Babel (CDN), mounts the app. |
| `matrixos.css` | The full design system (colors, shell, panels, topology, animations). |
| `matrixos-icons.jsx` | The inline SVG icon set (`window.MOS`). |
| `matrixos-app.jsx` | The app: sidebar, Overview, **AI Coder** (GitPilot repair loop), System. |
| `data.json` | Live snapshot written by `matrix-os dashboard` (falls back to demo data). |

## Run it

It's static, so any static server works:

```bash
cd frontend
python3 -m http.server 8080
# open http://localhost:8080
```

or use the helper:

```bash
bash frontend/serve.sh        # serves on http://localhost:8080
```

## Wire it to live matrix-os data

The Overview metrics, recent workflows, recent events, and system summary are
driven by `data.json`. Regenerate it from the real run log at any time:

```bash
matrix-os run "apply a code patch and run tests"   # produce some runs
matrix-os dashboard                                # writes frontend/data.json
```

Each field falls back to built-in demo content when absent, so the page always
looks complete — even before the first run. The **AI Coder** view renders the
GitPilot repair loop (Explore → Plan → Approve → Code → Review), the
`dry_run / draft_pr / apply` modes, the evidence bundle, and the autonomy
rollout — matching the contracts the kernel enforces.

## Design provenance

Recreated from the Claude Design handoff (`MatrixOS.html`): true Matrix (1999)
phosphor-green aesthetic, cinematic canvas rain, scanline glow, and a live
hub-and-spoke topology centered on Matrix Runtime. Motion can be toggled in
**System → Appearance** (persisted to `localStorage`).

"""Matrix OS command line interface.

    matrix-os run "<goal>" [--approve] [--json]   run the full governed loop
    matrix-os policy "<goal>" [--json]            show the decision without executing
    matrix-os validate                            self-check all contract schemas
    matrix-os doctor                              report config + reachability

Also runnable as ``python -m matrix_os``.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from . import __version__
from .config import Config
from .contracts import load_all_schemas
from .governance import Guardian
from .kernel import Kernel
from .planner import Planner
from .util import state_dir


def _print_run(record, as_json: bool) -> None:
    if as_json:
        print(json.dumps(record.to_dict(), indent=2, default=str))
        return
    print(f"run     : {record.run_id}")
    print(f"goal    : {record.goal}")
    print(f"risk    : {record.plan.get('risk')}")
    print(f"decision: {record.decision}")
    print(f"status  : {record.status}")
    print("reasons :")
    for r in record.reasons:
        print(f"  - {r}")
    print(f"evidence: {record.evidence['evidence_id']} ({record.evidence['summary']})")


def cmd_run(args) -> int:
    kernel = Kernel(Config.load())
    record = kernel.run(
        args.goal, approve=args.approve, repo=args.repo or None, allowed_paths=args.path
    )
    _print_run(record, args.json)
    # Non-zero exit when nothing useful ran, so scripts/CI can branch on it.
    return 0 if record.status in {"passed", "partial"} else 1


def cmd_policy(args) -> int:
    plan = Planner().plan(args.goal)
    grant = Guardian().evaluate(plan)
    if args.json:
        print(json.dumps({"plan": plan, "grant": grant}, indent=2, default=str))
        return 0
    print(f"goal    : {args.goal}")
    print(f"risk    : {plan['risk']}")
    print(f"decision: {grant['decision']}")
    print(f"allowed : {grant.get('allowed_capabilities')}")
    for r in grant.get("_reasons", []):
        print(f"  - {r}")
    return 0 if grant["decision"] not in {"deny", "emergency_stop"} else 2


def cmd_coder(args) -> int:
    """Exercise the live GitPilot AI-coder boundary (explicit, not the run loop)."""
    from .adapters import GitPilotCoder
    from .http_client import ServiceError

    coder = GitPilotCoder.from_config(Config.load())
    if args.action == "health":
        try:
            print(json.dumps(coder.health(), indent=2))
            return 0
        except ServiceError as exc:
            print(f"GitPilot unreachable at {coder.base_url}: {exc}")
            return 1

    # action == "dry-run"
    plan = coder.build_repair_plan(
        task_id=args.task,
        repo_url=args.repo,
        allowed_paths=args.path or [],
        mode="dry_run",
    )
    if not coder.reachable():
        print(f"GitPilot unreachable at {coder.base_url}; repair-plan built but not sent:")
        print(json.dumps(plan, indent=2))
        return 1
    try:
        resp = coder.repair(plan)
    except ServiceError as exc:
        print(f"repair call failed: {exc}")
        return 1
    if args.json:
        print(json.dumps(resp, indent=2))
    else:
        print(f"status    : {resp['status']}")
        print(f"risk_level: {resp.get('risk_level')}")
        print(f"changed   : {[f.get('path') for f in resp.get('changed_files', [])]}")
        print("patch_preview:")
        print(resp.get("patch_preview", "(none)"))
    return 0 if resp.get("status") in {"ok", "needs_approval"} else 1


def cmd_validate(args) -> int:
    schemas = load_all_schemas()
    for name in sorted(schemas):
        print(f"ok  contract {name}")
    print(f"validated {len(schemas)} contracts")
    return 0


def cmd_eval(args) -> int:
    from .evals import load_suite, run_suite

    report = run_suite(load_suite())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for c in report["cases"]:
            mark = "ok  " if c["passed"] else "FAIL"
            print(f"{mark} [{c['class']}] {c['name']}: "
                  f"{c['actual_decision']}/{c['actual_status']}")
        print(f"\n{report['passed']}/{report['total']} passed "
              f"(pass_rate={report['metrics']['pass_rate']}, "
              f"denial_rate={report['metrics']['policy_denial_rate']})")
    # Persist the report alongside run artifacts.
    out = state_dir() / "artifacts"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{report['report_id']}.json").write_text(json.dumps(report, indent=2))
    return 0 if report["failed"] == 0 else 1


def cmd_metrics(args) -> int:
    from .metrics import compute, load_runs

    m = compute(load_runs())
    print(json.dumps(m, indent=2))
    return 0


def cmd_dashboard(args) -> int:
    from .dashboard import build_dashboard, write_dashboard

    if args.json:
        print(json.dumps(build_dashboard(), indent=2))
        return 0
    out = write_dashboard()
    print(f"wrote dashboard snapshot -> {out}")
    return 0


def cmd_serve(args) -> int:
    from .server import serve

    serve(host=args.host, port=args.port)
    return 0


def cmd_doctor(args) -> int:
    cfg = Config.load()
    print(f"matrix-os {__version__}")
    print(f"safe_mode             : {cfg.safe_mode}")
    print(f"hitl_default          : {cfg.hitl_default}")
    print(f"autopilot_enabled     : {cfg.autopilot_enabled}")
    print(f"allow_production_deploy: {cfg.allow_production_deploy}")
    print(f"allow_self_modification: {cfg.allow_self_modification}")
    try:
        load_all_schemas()
        print("contracts             : ok")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"contracts             : FAILED ({exc})")
        return 1
    print("configured services   :")
    if not cfg.services:
        print("  (none — local components only)")
    for name, url in sorted(cfg.services.items()):
        print(f"  {name}: {url}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="matrix-os", description="Matrix OS kernel CLI")
    p.add_argument("--version", action="version", version=f"matrix-os {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the full governed-autonomy loop")
    run.add_argument("goal")
    run.add_argument("--approve", action="store_true", help="supply human approval")
    run.add_argument("--repo", default="", help="repo URL; enables GitPilot dry-run for code steps")
    run.add_argument("--path", action="append", help="allowed path for the coder (repeatable)")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=cmd_run)

    pol = sub.add_parser("policy", help="show the governance decision for a goal")
    pol.add_argument("goal")
    pol.add_argument("--json", action="store_true")
    pol.set_defaults(func=cmd_policy)

    coder = sub.add_parser("coder", help="exercise the GitPilot AI-coder boundary")
    coder.add_argument("action", choices=["health", "dry-run"])
    coder.add_argument("--repo", default="", help="repo URL for dry-run")
    coder.add_argument("--task", default="cli-dryrun", help="task id for dry-run")
    coder.add_argument("--path", action="append", help="allowed path (repeatable)")
    coder.add_argument("--json", action="store_true")
    coder.set_defaults(func=cmd_coder)

    val = sub.add_parser("validate", help="self-check all contract schemas")
    val.set_defaults(func=cmd_validate)

    ev = sub.add_parser("eval", help="run the behavioural eval suite")
    ev.add_argument("--json", action="store_true")
    ev.set_defaults(func=cmd_eval)

    met = sub.add_parser("metrics", help="aggregate metrics over recorded runs")
    met.set_defaults(func=cmd_metrics)

    dash = sub.add_parser("dashboard", help="write frontend/data.json from live run data")
    dash.add_argument("--json", action="store_true", help="print snapshot instead of writing")
    dash.set_defaults(func=cmd_dashboard)

    srv = sub.add_parser("serve", help="serve the console + backend API (auto port fallback)")
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8080)
    srv.set_defaults(func=cmd_serve)

    doc = sub.add_parser("doctor", help="report config and reachability")
    doc.set_defaults(func=cmd_doctor)

    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

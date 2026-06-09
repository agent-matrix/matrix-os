from matrix_os.config import Config
from matrix_os.contracts import validate
from matrix_os.evals import load_suite, run_suite
from matrix_os.kernel import Kernel
from matrix_os.metrics import compute


def test_core_suite_passes_and_is_contract_valid():
    report = run_suite(load_suite())
    validate("eval-report", report)
    assert report["total"] == report["passed"], (
        "core eval suite regressed: "
        + ", ".join(c["name"] for c in report["cases"] if not c["passed"])
    )
    assert report["metrics"]["pass_rate"] == 1.0


def test_metrics_over_a_few_runs():
    k = Kernel(Config.load())
    k.run("read and inspect the repository")     # allow / passed
    k.run("deploy to production")                # deny / cancelled
    k.run("apply a code patch and run tests")    # require_sandbox / passed

    runs = [
        {"decision": "allow", "status": "passed"},
        {"decision": "deny", "status": "cancelled"},
        {"decision": "require_sandbox", "status": "passed"},
    ]
    m = compute(runs)
    assert m["total_runs"] == 3
    assert m["policy_denial_rate"] == round(1 / 3, 4)
    assert m["execution_success_rate"] == round(2 / 3, 4)
    assert m["by_decision"]["deny"] == 1


def test_empty_metrics_are_safe():
    m = compute([])
    assert m["total_runs"] == 0
    assert m["policy_denial_rate"] == 0.0

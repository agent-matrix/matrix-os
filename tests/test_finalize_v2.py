from matrix_os.cognitive_kernel_v2 import CognitiveRunV2
from matrix_os.finalize_v2 import VerificationFinalizer


class Lab:
    def verify(self, **kwargs):
        return {
            "verdict": "pass",
            "sandbox_job_id": "sb1",
            "evidence_sha256": "abc",
            "checks": [{"criterion": "tests", "verifier": "pytest", "passed": True, "exit_code": 0}],
        }


class Memory:
    def __init__(self):
        self.writes = []
    def write(self, **kwargs):
        self.writes.append(kwargs)
        return kwargs


def test_verified_success_becomes_procedural_memory():
    run = CognitiveRunV2(
        "r1", "t1", "repair", "executing",
        plan={"plan_id": "p1"}, execution={"run_id": "h1"},
    )
    memory = Memory()
    out = VerificationFinalizer(matrixlab=Lab(), context=memory).finalize(
        run,
        repo_url="https://example.com/repo.git",
        ref="candidate",
        checks=[{"criterion": "tests", "verifier": "pytest", "command": "pytest -q"}],
        correctness=1.0,
        task_success=1.0,
        learning_summary="Run tests before applying the repair.",
    )
    assert out.run.status == "completed"
    assert out.evidence["verdict"] == "pass"
    assert [w["type"] for w in memory.writes] == ["episodic", "procedural"]

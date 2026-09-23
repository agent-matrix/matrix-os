from matrix_os.cognitive_kernel_v2 import CognitiveKernelV2


class Context:
    def retrieve(self, *a, **k):
        return [{"content": "prior lesson", "expert": "procedural"}]


class AI:
    def plan(self, goal, context=None, capabilities=None):
        return {
            "schema_version": "2.0",
            "plan_id": "p1",
            "goal": goal,
            "strategy": "test",
            "uncertainty": .2,
            "steps": [{
                "step_id": "s1", "objective": "inspect", "capability": "repo.read",
                "success_criteria": ["read"], "verifiers": ["check"], "risk": "low",
            }],
        }


class Guardian:
    def evaluate(self, plan):
        return {"grant_id": "g1", "plan_id": "p1", "decision": "allow", "allowed_capabilities": ["repo.read"]}
    def reasons(self, grant):
        return []


class Treasury:
    def grant(self, plan):
        return {"grant_id": "b1", "plan_id": "p1", "max_mxu": 1, "hard_stop": True}


class Architect:
    def compile(self, plan):
        return {"schema_version": "1.0", "graph_id": "wg1", "plan_id": "p1", "goal": plan["goal"], "nodes": [], "execution_policy": {}}


class Executor:
    def submit(self, **kwargs):
        return {"run_id": "hive1"}


def test_v2_kernel_keeps_authority_sequence():
    k = CognitiveKernelV2(
        ai=AI(), guardian=Guardian(), treasury=Treasury(), context=Context(),
        architect=Architect(), runtime=None, executor=Executor(),
    )
    out = k.run("inspect repository")
    assert out.status == "executing"
    assert out.execution["run_id"] == "hive1"


class HumanGuardian(Guardian):
    def evaluate(self, plan):
        return {"grant_id": "g1", "plan_id": "p1", "decision": "require_human_approval", "allowed_capabilities": ["repo.read"]}


def test_v2_kernel_stops_at_human_gate():
    k = CognitiveKernelV2(
        ai=AI(), guardian=HumanGuardian(), treasury=Treasury(), context=Context(),
        architect=Architect(), runtime=None, executor=Executor(),
    )
    out = k.run("inspect repository")
    assert out.status == "waiting_human"

from matrix_os.protocol_v2 import InvalidTransition, assert_transition, proof_obligations


def test_happy_path_transition():
    assert_transition("created", "observing")
    assert_transition("simulating", "compiling")
    assert_transition("learning", "completed")


def test_invalid_transition_is_blocked():
    try:
        assert_transition("created", "executing")
    except InvalidTransition:
        pass
    else:
        raise AssertionError("kernel accepted an authority-bypassing transition")


def test_plan_exposes_proof_obligations():
    plan = {"steps": [{"step_id": "s1", "success_criteria": ["tests pass", "no regression"]}]}
    assert list(proof_obligations(plan)) == ["s1: tests pass", "s1: no regression"]

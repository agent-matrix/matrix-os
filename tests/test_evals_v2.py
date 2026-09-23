from matrix_os.evals_v2 import RunMetrics, aggregate, compare


def test_safety_violations_reduce_score():
    clean = RunMetrics(1, 1, 0, 0, 3, 100, 1, 0.1)
    unsafe = RunMetrics(1, 1, 2, 0, 3, 100, 1, 0.1)
    assert clean.score() > unsafe.score()


def test_compare_reports_delta():
    a = RunMetrics(1, 1, 0, 0, 1, 10, 1, 0)
    b = RunMetrics(.5, .5, 0, 0, 1, 10, 1, 0)
    assert compare(a, b)["delta"] > 0


def test_aggregate_counts_runs():
    r = RunMetrics(1, 1, 0, 0, 1, 10, 1, 0)
    assert aggregate([r, r])["runs"] == 2

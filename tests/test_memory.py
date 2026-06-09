from matrix_os.config import Config
from matrix_os.kernel import Kernel
from matrix_os.memory import MemoryStore


def test_typed_and_scoped_retrieval(tmp_path):
    m = MemoryStore(path=tmp_path / "events.jsonl")
    m.write(type="episodic", scope="run", content="scanned the alpha repository", source="t")
    m.write(type="procedural", scope="policy", content="avoid deploying alpha to prod", source="t")
    m.write(type="semantic", scope="capability", content="alpha tests pass", source="t")

    only_proc = m.retrieve("alpha", type="procedural")
    assert len(only_proc) == 1 and only_proc[0]["type"] == "procedural"

    only_policy = m.retrieve("alpha", scope="policy")
    assert all(e["scope"] == "policy" for e in only_policy)


def test_blocked_run_writes_a_procedural_lesson():
    k = Kernel(Config.load())
    k.run("deploy to production now")  # critical -> denied
    lessons = k.memory.retrieve("deploy to production", type="procedural")
    assert lessons, "a denied run should leave a procedural lesson"
    assert "AVOID" in lessons[0]["content"]


def test_successful_run_writes_a_semantic_fact():
    k = Kernel(Config.load())
    k.run("read and inspect the repository")  # low -> passed
    facts = k.memory.retrieve("read and inspect", type="semantic")
    assert facts and "SUCCESS" in facts[0]["content"]


def test_lessons_persist_across_runs_in_the_same_store():
    k = Kernel(Config.load())
    k.run("deploy to production")
    # A later, related goal can retrieve the earlier lesson.
    before = len(k.memory.retrieve("production", type="procedural"))
    k.run("deploy app to production environment")
    after = len(k.memory.retrieve("production", type="procedural"))
    assert after >= before >= 1

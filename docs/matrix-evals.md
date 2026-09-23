# Matrix Evals / AM-Bench

Matrix Evals is the measurement plane for Agent-Matrix. The first implementation
lives inside Matrix OS only because the current GitHub connection cannot create a
new organization repository. The package boundary is intentionally extraction-ready.

## Rule

A run is not "intelligent" because it completed. It is measured against a baseline
on quality, safety, cost, human intervention and reliability.

Every governed run should eventually emit:

```
EvidenceBundle -> EvalReport -> LearningUpdate
```

## Promotion gate

A capability-changing update may advance only when it:

1. improves the target benchmark,
2. does not regress protected safety cases,
3. stays inside cost/risk budgets,
4. produces reproducible evidence,
5. passes Guardian policy,
6. receives human approval when policy requires it.

## Benchmark policy

AM-Bench must keep held-out tasks and must compare the full stack with simpler
baselines. Claims of emergent capability require a positive delta over the strongest
constituent baseline at a normalized resource budget.


## Live closed-loop finalization

When merged after the cognitive-kernel PR, `VerificationFinalizer` completes the
runtime loop:

```
Hive execution -> MatrixLab /verify -> EvidenceBundle v2
-> RunMetrics / EvalReport -> episodic memory -> procedural memory on verified success
```

Failed/uncertain runs never create procedural lessons. They are still recorded
episodically so later analysis can learn from failure without treating it as a
successful strategy.

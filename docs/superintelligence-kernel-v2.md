# Agent-Matrix cognitive kernel v2

This document freezes the authority model for the next Agent-Matrix architecture.

## One global orchestrator

**Matrix OS is the only component allowed to advance global run state.**

Services are deliberately narrower:

- Matrix AI proposes candidate strategies and emits `PlanIR v2`.
- Guardian decides what is allowed and emits a `PolicyGrant`.
- Treasury decides what is affordable and emits a `BudgetGrant`.
- Architect compiles an approved plan into a `WorkGraph`.
- Runtime/Hive execute the graph.
- MatrixLab verifies effects in isolation.
- Matrix Evals measures outcome quality.
- Matrix Context stores and retrieves typed memory.
- Humans retain authority over high-risk or capability-changing operations.

## State machine

```
CREATED -> OBSERVING -> REMEMBERING -> DISCOVERING -> DELIBERATING
-> GOVERNING -> FUNDING -> SIMULATING -> COMPILING -> EXECUTING
-> VERIFYING -> EVALUATING -> LEARNING -> COMPLETED
```

The kernel may pause at `WAITING_HUMAN`, revise after simulation, retry execution
after verification, or terminate as failed/cancelled/rolled_back. Every transition
is durable and replayable.

## Proof obligations

Every executable step declares success criteria and independent verifiers before
execution. A planner cannot mark its own work successful.

## Recursive improvement

Self-improvement is PR-only:

```
evidence -> eval -> hypothesis -> candidate change -> benchmark
-> policy review -> pull request -> human approval when capability-changing
```

No service may modify production policy, model weights, prompts, routing rules, or
its own executable code directly from a live run.

## Migration

V1 contracts remain supported during migration. V2 contracts are additive until
all live adapters and downstream services pass conformance tests.

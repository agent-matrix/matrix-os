# Matrix OS Architecture

Matrix OS joins independent Agent-Matrix services through explicit contracts and policies.

```text
Observe → Remember → Plan → Govern → Fund → Execute → Verify → Record → Learn
```

| Layer | Service | Responsibility |
|---|---|---|
| Model gateway | MatrixLLM / OllaBridge | Route model calls across local/cloud providers. |
| Memory | Matrix Context | Store, retrieve, inspect, and consolidate context. |
| Registry | Matrix Hub / Catalog | Discover agents, tools, MCP servers, and manifests. |
| Planning | Matrix AI | Produce PlanIR from goals and context. |
| Governance | Matrix Guardian | Enforce policy, risk, approval, and kill-switch rules. |
| Economy | Matrix Treasury | Enforce budget, spend, and resource constraints. |
| Execution | Matrix Architect | Execute approved code/system changes. |
| Durable workflow | Matrix Hive Driver | Run long-running workflows with evidence and retry. |
| Sandbox | MatrixLab | Test untrusted code/actions in disposable containers. |
| Runtime | Matrix Runtime | Run verified agents/tools/models in self-hosted infrastructure. |
| UI/CLI | Hub Admin, Matrix CLI, Matrix System | Operate and inspect the system. |

## Trust boundaries

Planner cannot execute. Executor cannot approve itself. Treasury cannot override policy. Sandbox cannot access production secrets. Memory cannot expose cross-tenant data. Agents cannot expand their own permissions.

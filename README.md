# Matrix OS

**Matrix OS** is the reference orchestration repository for the Agent-Matrix ecosystem: a governed, memory-aware, tool-using, safety-first AI operating system made from independent Matrix components.

It is intentionally **not** a giant monorepo. Matrix OS does not copy all application code from `matrix-hub`, `matrix-guardian`, `matrix-ai`, `matrix-architect`, `matrix-context`, `matrixlab`, `matrix-runtime`, or other Agent-Matrix projects. Instead, it defines the **architecture, contracts, policies, workflows, deployment manifests, agent roles, examples, and operating procedures** that make those components work as one system.

> Goal: build a practical, auditable, corrigible “alive” AI system that can observe, remember, plan, request approval, execute safely, verify outcomes, learn from results, and remain under human control.

---

## Why Matrix OS exists

The Agent-Matrix ecosystem already contains many specialized projects:

- **Matrix Hub**: catalog and installer for agents, tools, and MCP servers.
- **Matrix Context**: inspectable memory and context retrieval.
- **Matrix AI**: planning and reasoning service.
- **Matrix Guardian**: governance, risk, policy, health, and approvals.
- **Matrix Treasury**: budget and compute constraints.
- **Matrix Architect**: controlled code/system execution.
- **MatrixLab**: sandbox verification for untrusted code.
- **Matrix Runtime**: self-hostable execution plane.
- **Matrix Maintainer**: autonomous repository maintenance loop.
- **MatrixLLM**: model gateway and local/cloud model router.
- **Matrix Hub Admin / Network MatrixHub**: operator and discovery interfaces.

Matrix OS connects these into a single operating model:

```text
Observe → Remember → Plan → Govern → Fund → Execute → Verify → Record → Learn
```

The important design principle is separation of authority:

```text
Matrix AI         proposes plans
Matrix Guardian   decides what is allowed
Matrix Treasury   decides what can be afforded
Matrix Architect  executes approved work
MatrixLab         verifies in isolated sandboxes
Matrix Context    remembers and explains context
Matrix Hub        catalogs capabilities and evidence
Humans            retain authority over high-risk actions
```

---

## What this repository contains

```text
matrix-os/
├── README.md
├── docs/                         # architecture and operating model
├── compose/                      # Docker Compose profiles
├── k8s/                          # Kubernetes base + overlays
├── contracts/                    # JSON Schemas for system contracts
├── policies/                     # executable governance configuration
├── workflows/                    # YAML workflow definitions
├── agents/                       # role manifests for core Matrix agents
├── scripts/                      # bootstrap, run, health, eval scripts
├── examples/                     # concrete usage scenarios
└── .github/workflows/            # CI, security, eval, release pipelines
```

---

## System architecture

Matrix OS has eight layers.

### 1. Model gateway layer

Responsible for connecting to local and cloud foundation models.

Primary components:

- `matrix-llm`
- OllaBridge-compatible local model gateway
- optional OpenAI-compatible providers
- optional Anthropic, Google, IBM watsonx.ai, Ollama, Hugging Face, or enterprise models

Responsibilities:

- model routing
- fallback
- cost control
- privacy mode
- local-first execution
- provider abstraction
- request tracing

### 2. Memory and context layer

Responsible for long-term, inspectable, policy-aware memory.

Primary component:

- `matrix-context`

Memory types:

- semantic memory
- episodic memory
- procedural memory
- user memory
- project memory
- policy memory
- governance memory
- evidence memory

Core rule:

> No agent should act on important context that cannot be inspected, scoped, and traced.

### 3. Capability discovery layer

Responsible for finding agents, tools, MCP servers, workflows, and manifests.

Primary components:

- `matrix-hub`
- `catalog`
- `network.matrixhub`
- `mcp_ingest`
- `a2a-validator`

Responsibilities:

- capability search
- manifest validation
- version tracking
- install plans
- provenance
- trust metadata
- quality scoring

### 4. Planning layer

Responsible for turning a goal into a structured plan.

Primary component:

- `matrix-ai`

Output format:

- `contracts/plan-ir.schema.json`

A plan must describe:

- goal
- assumptions
- steps
- required capabilities
- expected artifacts
- risk level
- verification requirements
- rollback strategy

### 5. Governance kernel

Responsible for deciding whether a plan/action is permitted.

Primary component:

- `matrix-guardian`

Policy files:

- `policies/constitution.yaml`
- `policies/risk-matrix.yaml`
- `policies/capabilities.yaml`
- `policies/approval-rules.yaml`
- `policies/denylist.yaml`

Governance must enforce:

- human approval for high-risk operations
- capability allow/deny rules
- tenant and project isolation
- audit logging
- rollback requirements
- secret protection
- privacy restrictions
- unsafe-command blocking
- rate limits
- emergency stop

### 6. Economy and resource layer

Responsible for checking whether work is affordable.

Primary component:

- `matrix-treasury`

Contract:

- `contracts/budget-grant.schema.json`

Resources tracked:

- tokens
- compute minutes
- storage
- API calls
- runtime minutes
- sandbox jobs
- money-equivalent credits
- energy-equivalent MXU, if used

### 7. Execution and verification layer

Responsible for executing approved plans safely.

Primary components:

- `matrix-architect`
- `matrix-hive-driver`
- `matrixlab`
- `matrix-runtime`
- `MatrixShell`
- `matrix-maintainer`

Execution rules:

- no direct execution without a policy grant
- high-risk work must run in a sandbox first
- every run emits evidence
- every change must be reversible or explicitly marked irreversible
- self-improvement is allowed only through gated workflows

### 8. Human and operator interface layer

Responsible for observation, approval, intervention, and operation.

Primary components:

- `matrix-hub-admin`
- `network.matrixhub`
- `matrix-cli`
- `matrix-system`
- `matrix-protocol-helper`

Operators should be able to:

- inspect memory
- review plans
- approve/reject actions
- monitor running jobs
- examine evidence bundles
- replay decisions
- stop the system
- change policy

---

## Minimum viable alive loop

Matrix OS v0.1 should focus on one complete loop:

```text
1. User gives a goal.
2. Matrix Context retrieves relevant memory.
3. Matrix AI creates a PlanIR.
4. Matrix Guardian evaluates policy and risk.
5. Matrix Treasury checks budget.
6. Matrix Architect executes only approved steps.
7. MatrixLab verifies code/actions in sandbox.
8. Matrix Guardian checks evidence.
9. Matrix Hub stores artifacts and metadata.
10. Matrix Context remembers outcome.
```

This is the core of governed autonomy.

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/agent-matrix/matrix-os.git
cd matrix-os
```

### 2. Prepare local configuration

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```env
MATRIX_ENV=local
MATRIX_HUB_URL=http://localhost:7300
MATRIX_CONTEXT_URL=http://localhost:8088
MATRIX_AI_URL=http://localhost:7860
MATRIX_GUARDIAN_URL=http://localhost:8000
MATRIX_ARCHITECT_URL=http://localhost:8090
MATRIXLAB_URL=http://localhost:7070
MATRIX_LLM_URL=http://localhost:11435/v1
MATRIX_OPERATOR_TOKEN=change-me
```

### 3. Start safe local profile

```bash
bash scripts/bootstrap.sh
bash scripts/run-full-stack.sh safe
```

The safe profile starts only the minimum components needed for local evaluation. High-risk execution remains disabled by default.

### 4. Check health

```bash
bash scripts/healthcheck.sh
```

### 5. Run example loop

```bash
cd examples/safe-code-maintenance
bash run.sh
```

---

## Docker Compose profiles

This repository provides three Compose files.

### `compose/docker-compose.safe.yml`

Use this for demonstrations and safety testing.

Includes placeholders for:

- Matrix Context
- Matrix AI
- Matrix Guardian
- MatrixLab
- MatrixLLM

Execution defaults:

- no production secrets
- no host filesystem write access
- no automatic deployment
- HITL required for medium/high risk

### `compose/docker-compose.dev.yml`

Use this for local development and integration.

Adds:

- Matrix Hub
- Postgres
- Matrix System CLI environment
- Matrix Architect in dry-run mode

### `compose/docker-compose.full.yml`

Use this for integration testing of the full stack.

Adds:

- Matrix Treasury
- Matrix Runtime
- Matrix Maintainer
- Matrix Hub Admin
- optional Network MatrixHub

---

## Contracts

Matrix OS uses explicit JSON contracts so that each service can evolve independently.

Important contracts:

| Contract | Purpose |
|---|---|
| `plan-ir.schema.json` | Defines a structured plan from Matrix AI to Matrix Guardian / Architect. |
| `policy-grant.schema.json` | Defines what Guardian has approved. |
| `budget-grant.schema.json` | Defines what Treasury allows the run to spend. |
| `memory-event.schema.json` | Defines events written to Matrix Context. |
| `evidence-bundle.schema.json` | Defines logs/artifacts/proofs emitted after execution. |
| `agent-card.schema.json` | Defines agent identity, capabilities, protocols, safety profile, and endpoints. |

Every effectful operation should be traceable through these objects.

---

## Governance model

Matrix OS uses a safety constitution plus executable policies.

The constitution says what the system must preserve:

- human authority
- honesty
- privacy
- auditability
- reversibility
- least privilege
- legal and ethical compliance
- no hidden self-modification
- no unauthorized replication
- no unrestricted tool use
- no unapproved access to secrets

The policy engine then turns those principles into decisions:

```text
allow
allow_with_limits
require_human_approval
require_sandbox
deny
emergency_stop
```

High-risk actions must be blocked or approved by a human.

---

## Agent roles

The `agents/` folder defines the first core agents.

| Agent | Responsibility |
|---|---|
| `planner.agent.yaml` | Turns user goals into PlanIR. |
| `verifier.agent.yaml` | Checks outputs, tests, evidence, and regressions. |
| `maintainer.agent.yaml` | Maintains repositories through safe PR-based workflows. |
| `safety-reviewer.agent.yaml` | Reviews risk, policy, privacy, and misuse concerns. |
| `memory-curator.agent.yaml` | Writes, consolidates, expires, and explains memory. |

Agents do not grant themselves permissions. Permissions come from Guardian.

---

## Example workflows

### Observe → Plan → Approve → Execute → Verify

Defined in:

```text
workflows/observe-plan-approve-execute-verify.yaml
```

This is the main alive loop.

### Repository maintenance

Defined in:

```text
workflows/repo-maintenance.yaml
```

This loop scans a repository, creates a plan, asks approval, patches code, runs tests, and opens a PR.

### MCP validation

Defined in:

```text
workflows/mcp-validation.yaml
```

This loop validates a new MCP server before catalog publication.

### Gated self-improvement

Defined in:

```text
workflows/self-improvement-gated.yaml
```

This loop allows the system to propose improvements to itself only under strict simulation, sandboxing, evaluation, approval, and rollback requirements.

---

## Security defaults

Matrix OS is secure by default:

- high-risk actions require human approval
- shell commands are denied unless capability-granted
- secrets are never passed to untrusted sandboxes
- network access is disabled in sandbox mode unless explicitly allowed
- file writes are limited to configured workspaces
- production deployment is disabled unless explicitly enabled
- self-modification is PR-only by default
- every run must emit an evidence bundle
- emergency stop can disable all effectful workflows

---

## Suggested product roadmap

### v0.1 — Reference architecture

- create this repo
- define contracts
- define policies
- define safe local Docker profile
- implement one safe-code-maintenance demo
- document the alive loop

### v0.2 — Local working stack

- run Matrix Context, Guardian, AI, MatrixLab, and MatrixLLM locally
- validate PlanIR → PolicyGrant → EvidenceBundle flow
- add mock services for unavailable components
- add CI integration tests

### v0.3 — Repository maintainer product

- integrate Matrix Maintainer
- add GitHub PR workflow
- add Guardian approvals
- add MatrixLab verification
- add memory learning from merged/rejected PRs

### v0.4 — Enterprise deployment

- Kubernetes overlays
- multi-tenant secrets
- SSO-ready admin console
- audit export
- budget controls
- compliance reports

### v1.0 — Matrix OS Reference Release

- full observe-plan-approve-execute-verify loop
- self-hosted deployment
- documented threat model
- reproducible eval suite
- agent certification workflow
- marketplace/catalog integration

---

## What Matrix OS is not

Matrix OS is not:

- a single gigantic application
- an unrestricted autonomous agent
- a replacement for human governance
- a black-box “AGI” claim
- a model training framework
- a tool for bypassing safety controls

Matrix OS is:

- a reference orchestration layer
- a safety and governance blueprint
- an integration repo
- an enterprise deployment template
- a practical route toward governed autonomous AI systems

---

## License

Apache-2.0, unless a referenced upstream component states otherwise.

---

## Final thought

The first product should not be marketed as “superintelligence.” The first product should be:

> **Safe autonomous software maintenance with memory, approvals, sandbox verification, and audit trails.**

From there, Matrix OS can grow into the governed operating system for autonomous AI.

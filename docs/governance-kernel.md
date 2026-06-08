# Governance Kernel

The Governance Kernel is the safety and permission system of Matrix OS.

Inputs: PlanIR, agent identity, user identity, scope, capabilities, risk score, tool targets, budget request, environment mode.

Outputs: allow, allow_with_limits, require_human_approval, require_sandbox, deny, emergency_stop.

Non-negotiable rules: high-risk actions require approval; untrusted code runs in MatrixLab; self-modification is PR-only; every effectful action emits evidence; emergency stop overrides all workflows.

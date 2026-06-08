# Execution Loop

1. Receive PlanIR
2. Validate schema
3. Request PolicyGrant from Guardian
4. Request BudgetGrant from Treasury
5. Compile plan into execution graph
6. Run low-risk steps directly or via Matrix Runtime
7. Run untrusted/high-risk steps in MatrixLab
8. Capture EvidenceBundle
9. Verify evidence
10. Record outcome and memory

Execution modes: dry_run, sandbox, approved, production.

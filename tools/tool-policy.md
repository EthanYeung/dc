# Tool Selection Policy

Workers choose their own tools to accomplish goals, subject to role permissions.

Preferred order:
1. API or SDK.
2. CLI or deterministic programmatic tool.
3. Structured browser automation.
4. Visual computer use.

Use the highest layer that is reliable for the task. Visual computer use is a universal fallback, not the default.

For every consequential state-changing action:
- inspect current state;
- run policy check;
- execute;
- verify the external result;
- log the action and evidence.

Never infer success solely from a click, command submission or HTTP request being attempted.

## Real-world experiment gate

Before a first live transaction, classify operational exposure and present the
exact experiment, evidence, terms, finite per-experiment caps, and a documented
plausible-loss estimate for a separate Founder decision. `policy_engine.assess_exposure()` reports review
readiness only; it never authorizes execution. Class B also needs documented,
independent domain-appropriate review. Class C is prohibited and must not be
escalated as an ordinary approval request.

The current policy engine does not authenticate evidence, reviewer identity,
or Founder approval records. Until a trusted approval-verification path is
integrated, do not execute an external action whose decision requires Founder
approval. Unknown action names and unmapped risk flags fail closed. Cash-spend
limits do not cap contractual or account-recovery exposure.

An action label supplied by a worker is not a trusted tool identity. A future
execution gateway must bind canonical action IDs to the actual tool operation
and verify the exact Founder approval record; this repository does not yet
provide that binding. Until then `evaluate_action()` never authorizes execution
from a self-reported label: `internal_reversible_operation` is denied with
`trusted_action_binding_unavailable`.

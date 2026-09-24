# Runtime

The runtime layer turns company decisions into authorized worker execution.

## Source of truth

- SQLite: current company facts, experiments, evidence metadata, ledger, risks and action audit.
- Hermes persistent task queue: who is doing what.
- Git: constitution, role context, playbooks, durable evidence and assets.
- Hermes memory: worker-specific learned context, never the sole source of company truth.

## Worker execution contract

A worker receives:
- role;
- goal;
- linked hypothesis/experiment;
- relevant state snapshot;
- budget/timebox;
- allowed tool and credential scope;
- success/failure/stop criteria.

It then runs:

OBSERVE -> PLAN -> POLICY CHECK -> ACT -> VERIFY -> RECORD -> HANDOFF

Workers choose their own tools. The control plane specifies outcomes and boundaries, not click-by-click instructions.

## Events

Important runtime events should wake the appropriate role:
- experiment.completed
- evidence.created
- payment.received
- deployment.failed
- risk.threshold_exceeded
- approval.resolved

The allocator also performs periodic reconciliation to catch missed events and stale work.

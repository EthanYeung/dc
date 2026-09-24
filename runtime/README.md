# Runtime

The runtime layer turns company decisions into authorized worker execution.

## Source of truth

- SQLite: current company facts, work state, experiments, evidence metadata, ledger, assets, risks and action audit.
- Hermes persistent task queue: worker-facing work delivery.
- Git: constitution, role context, playbooks, durable evidence and asset artifacts.
- Hermes memory: worker-specific learned context, never the sole source of company truth.

## Worker execution contract

A persistent worker receives:
- worker identity / role;
- work-item ID;
- goal;
- linked opportunity / venture / hypothesis / experiment;
- relevant state snapshot;
- budget/timebox;
- allowed tool and credential scope;
- success/failure/stop criteria.

It then runs:

OBSERVE -> PLAN -> DELEGATE(optional) -> POLICY CHECK -> ACT -> VERIFY -> RECORD -> HANDOFF

Workers choose their own tools. The control plane specifies outcomes and boundaries, not click-by-click instructions.

## Persistent workers and subagents

Persistent workers are long-lived Hermes profiles and may own work items.

Subagents are temporary child executions created within a WorkerRun. They:
- receive a bounded purpose and narrow context;
- have no independent budget or approval authority;
- cannot expand the parent role's permission scope;
- return artifacts/results to the parent;
- do not directly change authoritative company state.

The parent worker verifies subagent output and owns the final handoff.

## Runtime trace

Every execution should be traceable:

```text
Directive
-> WorkItem
-> WorkerRun
-> optional SubagentRun(s)
-> Evidence / Asset / Action
-> Event
-> next Worker or Allocator
```

## Events

Important runtime events should wake the appropriate role:
- work.completed
- experiment.completed
- evidence.created
- asset.created
- commercial_signal.observed
- payment.received
- deployment.failed
- risk.threshold_exceeded
- approval.requested
- approval.resolved

Events require idempotency keys.

The allocator also performs periodic reconciliation to catch missed events and stale work.

## Concurrency and recovery

Use leases for:
- work-item claims;
- allocator reconciliation;
- duplicate-sensitive side effects.

Runs need heartbeat/expiry handling. A stale run may be recovered only after verifying whether external side effects occurred.

Retries of consequential external actions require idempotency or explicit human/worker verification.

# Worker Model

## Principle

A company role is not a prompt.

```text
PersistentWorker
= Identity
+ Goal
+ Memory
+ Workspace
+ Runtime
+ Tools
+ Credential Scope
+ Permission Scope
+ Task Queue
+ Accountability
```

DC begins with five persistent workers:
- allocator;
- research;
- builder;
- growth;
- auditor.

Each persistent worker should map to a long-lived isolated Hermes profile.

## Persistent worker vs subagent

### Persistent worker

A persistent worker:
- has a stable company role;
- can own work items;
- has durable role memory;
- has an explicit permission envelope;
- can be audited across runs;
- can create evidence and durable handoffs;
- is accountable for verifying its final output.

### Subagent

A subagent:
- exists only inside a parent worker run;
- performs a bounded delegated subtask;
- does not own company strategy or state;
- does not receive independent economic authority;
- should not receive master credentials;
- returns an artifact/result to the parent;
- ends when the delegated work is complete.

Subagents are parallel compute, not additional management layers.

## Delegation authority

A parent worker may delegate when expected benefit from parallelism or specialization exceeds delegation overhead.

Effective subagent permissions are:

```text
parent role permissions
INTERSECT delegated task scope
INTERSECT subagent safety ceiling
```

A subagent cannot expand the parent's authority.

Consequential actions must route through the parent worker and deterministic policy layer.

## Accountability chain

Every durable result should be traceable:

```text
Directive
-> WorkItem
-> WorkerRun
-> optional SubagentRun(s)
-> Artifact / Evidence
-> Verified Handoff
-> Event / Decision
```

The parent worker is accountable for:
- checking subagent output;
- resolving conflicting subagent results;
- removing duplicates;
- distinguishing evidence from inference;
- verifying external effects;
- producing the final structured handoff.

## Concurrency

Persistent workers may run concurrently on independent authorized work.

Use leases for:
- work-item claims;
- allocator reconciliation;
- irreversible or duplicate-sensitive external actions.

Subagent parallelism should be bounded per worker run to prevent uncontrolled cost and redundant work.

## Failure handling

Interrupted or failed runs must not imply task failure or external-action failure.

Runtime should record:
- run state;
- last heartbeat;
- output artifact, if any;
- error summary;
- external side-effect references;
- whether retry is safe.

Retries of consequential actions require idempotency controls.

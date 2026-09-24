# Architecture

DC is intentionally not modeled after a conventional org chart. It is a constrained economic control system with autonomous digital workers.

## Four-layer model

```text
1. PEOPLE — persistent company identities
   Founder
   Allocator / CEO
   Research
   Builder
   Growth
   Auditor

              execute

2. WORK — temporary execution
   Directive
   WorkItem / Task
   WorkerRun
   SubagentRun
   Experiment
   Event
   Approval
   Lease

              changes

3. BUSINESS — economic state
   Opportunity
   Audience
   Venture
   CommercialSignal
   Customer / Counterparty
   Revenue / Cost
   Evidence

              creates / improves

4. ASSETS — what survives the work
   DistributionAsset
   SoftwareAsset
   DataAsset
   BrandAsset
   WorkflowAsset
   CustomerRelationship
   KnowledgeAsset
```

Workers execute work. Work changes business state. Business activity creates durable assets. Durable assets should increase future earning power.

## Control plane

```text
Founder
  |
  | objective / constraints / capital / kill switch
  v
+-----------------------+
| Capital Allocator     |
| (control plane)       |
+-----------+-----------+
            |
            | next-best-action / authorized work
            v
+-----------------------+
| Experiment Engine     |
| hypothesis -> test    |
+-----------+-----------+
            |
     +------+------+------+
     |             |      |
     v             v      v
 Research       Builder  Growth
     |             |      |
     |      optional bounded
     |         subagents
     |             |      |
      \            |     /
       +-------- Real World
                 |
      users / revenue / costs / behavior
                 |
                 v
        Evidence + Ledger + Assets
                 |
                 v
              Auditor
                 |
                 +-----> Allocator
```

A deterministic policy layer surrounds all state-changing actions.

## Worker identity model

Persistent workers are long-lived Hermes profiles. They own role responsibility and task accountability.

Subagents are ephemeral children of a persistent worker:
- they are execution helpers, not company employees;
- they have no independent budget or approval authority;
- their effective permission scope is narrower than or equal to the parent worker;
- consequential actions are returned to the parent worker for policy check and execution.

## Design principles

1. Goal-driven, not procedure-driven.
2. Event-driven first; periodic reconciliation second.
3. External evidence dominates model consensus.
4. Capital is released progressively with evidence.
5. Deterministic code enforces hard limits.
6. Worker cognition, runtime environment, browser identity and credentials are independently scoped.
7. Persistent worker identity is separate from temporary subagent capacity.
8. API > CLI > structured browser > visual computer use.
9. A worker verifies effects after acting.
10. Company state survives loss of all chat/session history.
11. Founder attention is reserved for exceptions and constitutional decisions.
12. Durable assets are tracked by ownership, economics, dependency and reuse value rather than by file existence alone.

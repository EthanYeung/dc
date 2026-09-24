# Architecture

DC is intentionally not modeled after a conventional org chart. It is a constrained economic control system with autonomous digital workers.

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
     \             |      /
      \            |     /
       +-------- Real World
                 |
      users / revenue / costs / behavior
                 |
                 v
        Evidence + Ledger
                 |
                 v
              Auditor
                 |
                 +-----> Allocator
```

A deterministic policy layer surrounds all state-changing actions.

## Design principles

1. Goal-driven, not procedure-driven.
2. Event-driven first; periodic reconciliation second.
3. External evidence dominates model consensus.
4. Capital is released progressively with evidence.
5. Deterministic code enforces hard limits.
6. Worker cognition, runtime environment, browser identity and credentials are independently scoped.
7. API > CLI > structured browser > visual computer use.
8. A worker verifies effects after acting.
9. Company state survives loss of all chat/session history.
10. Founder attention is reserved for exceptions and constitutional decisions.

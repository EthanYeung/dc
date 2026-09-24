# Hermes Runtime Integration

Hermes is the worker runtime; DC owns company policy, state, economic logic and durable business identity.

## Persistent workers are not subagents

DC has five persistent company workers:

- allocator
- research
- builder
- growth
- auditor

Each persistent worker maps to an isolated long-lived Hermes profile.

A persistent worker is a company identity with durable responsibility, memory, workspace, task ownership and a bounded permission envelope.

A Hermes subagent is temporary execution capacity created by a persistent worker for a bounded subtask. A subagent is not a company role, does not own company state, and does not receive independent budget, credentials or approval authority.

Conceptually:

```text
DC persistent worker
  -> may spawn bounded subagents
       -> perform delegated analysis / implementation / read-only research
       -> return artifacts to parent worker
  -> parent worker verifies result
  -> parent worker performs any consequential company action through policy controls
```

## Persistent worker profiles

Create isolated Hermes profiles for:
- allocator
- research
- builder
- growth
- auditor

Each profile should have:
- its own persistent memory;
- its own work directory/context;
- a separate browser profile where login state is needed;
- only the tool and credential scopes required by the role;
- the worker model selected through deployment configuration (logical default: `gpt6-luna-max`; map this to the exact provider model ID available in your environment).

## Subagent delegation rules

Subagents are optional. A worker should spawn them only when parallelism or specialization is likely to reduce time-to-learning or execution cost.

Effective subagent authority must be no broader than the intersection of:
1. the parent worker's role permissions;
2. the specific delegated task scope;
3. the platform's safe subagent maximum.

Subagents may commonly:
- analyze documents or code;
- perform bounded public-web research;
- generate draft artifacts;
- run local tests;
- compare alternatives.

Subagents must not independently:
- spend or commit money;
- access master or broad credentials;
- change company state;
- approve work;
- modify constitution or policy;
- perform irreversible external actions;
- deploy to production unless the parent worker and policy layer explicitly authorize the exact action.

Consequential actions route back through the persistent parent worker and deterministic policy engine.

## Isolation

Profile isolation separates worker cognition/state. Runtime isolation separates worker execution.

Where practical, give each persistent worker an isolated container or VM workspace. Do not share mutable browser state or unrestricted production credentials across roles.

Subagents should inherit only the minimum temporary workspace/tool scope needed for the delegated task.

## Scheduling

Use two trigger classes:
- event driven: experiment completion, payment, deployment failure, risk breach, customer event;
- periodic reconciliation: allocator heartbeat to compare company state, ledger, active experiments and opportunity queue.

The heartbeat is a safety/reconciliation mechanism, not a substitute for event-driven execution.

## Work handoff

Use Hermes' persistent task mechanism as the work queue. Company business state remains in the DC database.

A work item should include:
- goal;
- linked opportunity / venture / hypothesis / experiment;
- allowed budget;
- timebox;
- success/failure criteria;
- relevant artifact paths;
- required approval state;
- permitted tool/credential scope.

Each persistent worker run and subagent run should receive a durable run ID so evidence and artifacts can be traced back to execution.

## Tool access

Prefer API/CLI integrations. Expose browser and computer-use capabilities where required. Route credential retrieval through an external secret manager or narrow runtime adapter; never place secrets in profile memory or repository context.

## Next integration milestone

Implement a thin DC runtime adapter that:
1. reads the next authorized work item;
2. claims it with a lease;
3. injects relevant company context into the persistent worker;
4. records worker/subagent run IDs;
5. runs deterministic policy checks before consequential actions;
6. writes evidence/action results back to the database;
7. emits idempotent events for the allocator or next responsible worker;
8. recovers stale leases and interrupted work safely.

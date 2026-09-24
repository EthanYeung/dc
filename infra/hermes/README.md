# Hermes Runtime Integration

Hermes is the worker runtime; DC owns company policy, state and economic logic.

## Persistent worker identities

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

## Isolation

Profile isolation separates worker cognition/state. Runtime isolation separates worker execution.

Where practical, give each worker an isolated container or VM workspace. Do not share mutable browser state or unrestricted production credentials across roles.

## Scheduling

Use two trigger classes:
- event driven: experiment completion, payment, deployment failure, risk breach, customer event;
- periodic reconciliation: allocator heartbeat to compare company state, ledger, active experiments and opportunity queue.

The heartbeat is a safety/reconciliation mechanism, not a substitute for event-driven execution.

## Work handoff

Use Hermes' persistent task mechanism as the work queue. Company business state remains in the DC database.

A work item should include:
- goal;
- linked hypothesis/experiment;
- allowed budget;
- timebox;
- success/failure criteria;
- relevant artifact paths;
- required approval status.

## Tool access

Prefer API/CLI integrations. Expose browser and computer-use capabilities where required. Route credential retrieval through an external secret manager or narrow runtime adapter; never place secrets in profile memory or repository context.

## Next integration milestone

Implement a thin DC runtime adapter that:
1. reads the next authorized work item;
2. injects relevant company context into the worker;
3. runs deterministic policy checks before consequential actions;
4. writes evidence/action results back to the database;
5. emits an event for the allocator when a gate is reached.

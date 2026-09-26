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

## INFRA-002 simulated approval gateway

`runtime/approval_gateway.py` adds a fail-closed execution path for testing. A
persisted `ApprovalRecord` binds the experiment, one canonical action, one
non-empty offer ID, one non-empty channel ID, risk class, Founder decision,
evidence references, timebox, and transaction/spend/attention/labor caps. The
record's canonical JSON, including UTC timestamps at whole-second precision, is
verified with Ed25519 against public keys supplied by trusted bootstrap code; no
signing private key or production public-key configuration is stored in this
repository.
The older unsigned `approvals` queue is not an execution credential.
The gateway obtains an authenticated principal ID, role, and worker-run ID from
a trusted principal provider, checks the request claims against that identity,
and stores the principal/run binding in the attempt digest and audit row. The
request's `actor_role` and `worker_run_id` are not authority sources. Idempotent
replays repeat identity, role, kill-switch, and approval checks before returning
any stored result; a different principal or run cannot retrieve it.

Before an external stub can run, the gateway verifies the signature and decision,
checks exact scope and expiry, re-assesses GOV-001 exposure (Class C remains
prohibited), checks the policy engine and cumulative caps, then checks the
database-backed kill-switch gate and reserves an immutable audit attempt. A request
names only a canonical action ID; it cannot provide a tool callable or mark itself
internal. Internal public research, local code changes, tests, Git artifacts,
read-only inspection, and non-consequential analysis remain approval-free only
through their trusted internal bindings. These are bootstrap-owned in-process
handlers, not external adapters; only external actions are restricted to the
no-I/O simulator. Internal requests cannot claim experiment scope or external
attention/labor usage; cumulative experiment and approval caps count only
allowed external attempts with an approval binding. Kill-switch state is stored
in a shared SQLite control row and defaults to active. The optional constructor value initializes only a missing
control row; an existing row remains authoritative across restarts. State changes
must use explicit `activate()` or `deactivate()` calls from trusted control-plane
code, never worker handlers. Activation commits immediately; requests already
admitted at the execution boundary may finish. Gateways sharing the database,
including separate processes and restarts, observe the same state. Direct database
writers can still bypass this application-path control, as noted below.

The external registry and gateway accept only the exact built-in
`SimulatedExternalTool`, a no-I/O result stub. The gateway validates bindings
from any provider before reservation and again at final admission, rejecting
arbitrary callables even when marked `simulation_only`. This initial build cannot
invoke a live external adapter. Simulator observers are limited to exact built-in
lists, and recording uses built-in list operations rather than overridable hooks.
This includes `record_payout_state`: it is not wired to a live
cash engine, payment processor, or payout operation. When INFRA-001 is integrated,
that action must bind to its verified transition entry point rather than direct
SQL writes. `execution_attempts`, `execution_results`, `execution_events`, and
`execution_attempt_relations`
record allowed, denied, replayed, and completed attempts; requests store only a
digest of payload data. Failed or ambiguous external attempts continue to consume
the approved cap, and idempotency prevents a replay from executing twice.
At gateway entry, each request is detached into a gateway-owned command. Text
fields are length-checked before trimming and capped at 4 KiB aggregate UTF-8;
finite, non-negative amount fields are also validated. Amounts are normalized
to bounded `Decimal` values (at most 256 coefficient digits,
exponents from -128 through 128, and adjusted exponent at most 128). Plain-JSON
payloads are copied and recursively frozen with a 64 KiB UTF-8 text budget,
256 KiB canonical-JSON budget, 4,096-item limit, 32-level nesting limit, and
256-bit integer limit. The digest, authorization, reservation, and handler use
that same snapshot. Cumulative cap arithmetic uses exact fixed-scale integer
units rather than the ambient Decimal context. Unauthenticated and
malformed-shape denials use server-generated idempotency keys, so caller-chosen
keys remain available to a later valid request.
Idempotency collisions are recorded as detached denials and return no attempt
ID; immutable relation rows store digests of the target attempt and collision
key for audit without modifying or disclosing the target attempt. Malformed
requests with a safe caller key also record this digest-only relation when that
key already exists. Authenticated cross-principal collisions use the same
detached path.
`ExecutionOutcome.allowed` means authorization passed, not that the tool result
was successfully persisted or verified; callers must inspect `status` and
`result` before treating an action as complete. A committed reservation event is
written to the configured SQLite database before invocation; persistence durability
depends on SQLite and filesystem settings. If result storage fails, the gateway
records the failure when the database remains writable and never re-executes that
idempotency key. Handler-provided result references are never persisted or
returned; verified outcomes use the gateway-generated `gateway-result:<attempt_id>`
reference instead.

These are application-path guardrails, not a production trust boundary. SQLite
does not authenticate workers, a process with database write access can bypass
triggers or falsify audit rows, and the code does not provide a Founder signing
service or live external adapters. Do not use this gateway for real marketplace,
KYC, customer-contact, payment, payout, spending, or production actions.

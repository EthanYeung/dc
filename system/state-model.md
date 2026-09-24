# Company State Model

The database is the source of truth for current operational facts. Git stores durable policy, knowledge, code, decisions and evidence artifacts.

## Four state layers

### People
- Worker: persistent company identity mapped to a long-lived Hermes profile.

### Work
- WorkItem: bounded authorized task owned by one persistent worker.
- WorkerRun: one execution attempt by a persistent worker.
- SubagentRun: temporary delegated execution inside a WorkerRun.
- Experiment: bounded action designed to update belief.
- Event: idempotent signal that may wake another role.
- Approval: explicit authorization request for an action outside autonomous limits.
- Lease: temporary claim preventing duplicate execution.

### Business
- CompanyState: objective, operating mode, strategy mode, capital envelope, last reconciliation.
- Opportunity: candidate problem/customer/business-model combination.
- Audience: clearly defined target-user group and qualification rule.
- Venture: an opportunity that passed investment gates and now receives operating capital.
- CommercialSignal: observed behavior indicating meaningful intent beyond passive traffic.
- Hypothesis: falsifiable claim linked to an opportunity or venture.
- Evidence: externally verifiable observation with provenance and quality level.
- Decision: capital-allocation choice and rationale.
- LedgerEntry: revenue, expense, commitment or transfer.
- Risk: identified risk, severity, owner and mitigation.

### Assets
- DistributionAsset: repeatable channel, utility, data surface or direct relationship improving future access to qualified users.
- Asset: reusable software, data, workflow, brand, customer relationship, knowledge or other economic asset.

## Distribution state

The system should be able to answer:
- Which audiences can the company reach repeatedly?
- Which channels are owned, rented or hybrid?
- How many users are qualified rather than merely visible?
- Which users return?
- Which relationships are direct and permissioned?
- Which channels create commercial signals?
- What is the cost per qualified user?
- Which distribution assets continue producing value with low incremental effort?

## Operating state

The system should also be able to answer:
- Which persistent workers exist and which Hermes profile maps to each?
- Which work items are ready, running, blocked or done?
- Which worker run owns a task lease?
- Which subagents were spawned and by which parent run?
- Which events remain unconsumed?
- Which actions await approval?
- Which runs are stale and safe to retry?

## Asset state

For each material asset the company should know:
- provenance;
- owner or linked venture;
- creation and maintenance cost;
- attributable economic value where measurable;
- platform dependency;
- reuse scope;
- current status.

Operational state must be reconstructible without relying on an agent conversation history.

# Company State Model

The database is the source of truth for current operational facts. Git stores durable policy, knowledge, code, decisions and evidence artifacts.

Core entities:

- CompanyState: objective, operating mode, strategy mode, capital envelope, last reconciliation.
- Opportunity: a candidate problem/customer/business-model combination.
- Audience: a clearly defined target-user group and qualification rule.
- DistributionAsset: a repeatable channel, utility, data surface or direct relationship that improves future access to qualified users.
- CommercialSignal: observed behavior indicating meaningful intent beyond passive traffic.
- Hypothesis: a falsifiable claim linked to an opportunity or venture.
- Experiment: a bounded action designed to update belief.
- Evidence: externally verifiable observation with provenance and quality level.
- Venture: an opportunity that passed investment gates.
- Metric: time-series business measurement.
- Action: a consequential external or internal operation.
- Decision: a capital-allocation choice and its rationale.
- LedgerEntry: revenue, expense, commitment or transfer.
- Asset: reusable economic asset created or acquired.
- Risk: identified risk, severity, owner and mitigation.

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

Operational state must be reconstructible without relying on an agent conversation history.

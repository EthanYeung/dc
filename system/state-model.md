# Company State Model

The database is the source of truth for current operational facts. Git stores durable policy, knowledge, code, decisions and evidence artifacts.

Core entities:
- CompanyState: objective, mode, capital envelope, last reconciliation.
- Opportunity: a candidate market/problem/business model.
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

Operational state must be reconstructible without relying on an agent conversation history.

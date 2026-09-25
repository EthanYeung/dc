# Experiment Contract

Every experiment must specify:
- id;
- linked opportunity/venture;
- hypothesis;
- primary uncertainty;
- expected information gain;
- expected economic upside if true;
- budget cap;
- timebox;
- required tools;
- success criteria;
- failure criteria;
- stop conditions;
- evidence collection method;
- owner;
- reviewer.

## Operational exposure and approval

Before any real-world action or transaction, assign an exposure class and attach
the applicable platform/contract terms and a risk assessment. The approval
request must include the maximum transaction count and value, direct cash
spend, Founder attention, delivery labor, duration, named offer/channel, stop
conditions, reversal/refund/dispute response, and a documented estimate of
plausible maximum loss with its evidence and residual-risk assumptions. The
loss estimate is not a contractual liability cap. Set numeric limits for that
experiment; the existing autonomous cash-spend ceilings are not contractual
liability caps.

- **Class A — bounded, standardized exposure:** one named offer and channel, at
  most one transaction, finite per-experiment limits, standardized terms
  accepted as-is (no negotiating away or bypassing platform safeguards), no
  recurring commitment, sensitive data, or regulated professional advice, and
  verified operational containment. An exact contractual aggregate-liability
  ceiling is not a prerequisite by itself. A Class A result only means the
  proposal may be sent to the Founder; explicit, experiment-specific Founder
  approval is still required before the first live transaction.
- **Class B — material or ambiguous exposure:** material indemnity, refund or
  chargeback risk, sensitive data, regulated advice, uncertain contracting
  entity, recurring obligations, nonstandard terms, or unresolved legal/tax,
  payout, or surviving-obligation questions. Require documented independent,
  domain-appropriate review (reviewer role, evidence reference, findings, and
  residual risk) and explicit Founder approval before any action. If no exact
  contractual liability cap exists, that review must verify credible liability
  containment; if it cannot, the proposal is not ready for a positive Founder
  decision and may be Class C when no credible containment exists.
- **Class C — prohibited exposure:** borrowing/credit, personal guarantees,
  asset pledges, custom intentionally uncapped liability, material downside
  without credible containment, deception/unlawful conduct, or policy bypass.
  An individual experiment approval cannot waive Class C.

The deterministic classifier checks the shape and completeness of submitted
facts. It does not authenticate evidence, reviewer identity, or a Founder
decision. `assess_exposure()` returns review eligibility only and always sets
`execution_authorized` to false. Until a trusted Founder-approval record and
verification path and trusted action-to-tool binding are integrated,
policy-engine execution remains fail-closed. A self-reported
`internal_reversible_operation` label is not enough to authorize an operation.

## Default behavior

Run the smallest experiment that can materially change the decision.

Do not build a full product to answer a question that a landing page, prototype, customer interview, price test or manual service can answer more cheaply.

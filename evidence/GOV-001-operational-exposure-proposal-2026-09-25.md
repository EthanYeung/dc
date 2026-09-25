# GOV-001 — Bounded Operational Exposure Proposal

- Date: 2026-09-25
- Status: governance proposal on `governance/gov-001-operational-exposure`; not merged and not an authorization to act.
- Linked directive: GitHub Issue #6, `[GOV-001] Define bounded operational exposure for real-world experiments`.
- Scope: policy text, deterministic review-readiness code, tests, and a migration review of CEO-004. No account, KYC, listing, customer contact, payment, spend, or delivery action is authorized.

## Proposed rule

Workers may not autonomously accept materially unlimited or uncontrolled liability. A standardized platform contract with no exact aggregate-liability ceiling is not automatically prohibited, but it is not automatically safe either. A proposal must be classified A/B/C from the terms, transaction structure, downside, evidence, and containment—not from the worker's description alone.

A classifier result is a routing decision only. Class A and B still require a specific written Founder decision before the first live transaction. Class C cannot be waived by an individual experiment approval.

## Exposure classes

| Class | Rule | Required gate |
|---|---|---|
| A — bounded, standardized | Standardized terms accepted as-is, with no negotiating away or bypassing platform safeguards; one offer, one channel, and at most one transaction; explicit finite experiment-specific transaction-value, direct-spend, Founder-attention, delivery-labor, and timebox caps; a documented estimated maximum plausible loss and residual-risk basis; stop and reversal/refund/dispute plans; verified operational containment; no custom indemnity, recurring commitment, sensitive data, or regulated professional advice. | Eligible only to be submitted for explicit Founder review. A precise contractual aggregate-liability ceiling is not a prerequisite by itself. Founder must judge whether the stated caps and residual downside are genuinely small and acceptable. |
| B — material or ambiguous | Material indemnity, refunds/chargebacks, sensitive data, regulated advice, unclear contracting entity, recurring obligations, nonstandard terms, material legal/tax uncertainty, unclear surviving obligations, unverified payout path, or multiple transactions. | Documented independent, domain-appropriate review plus explicit, experiment-specific Founder approval before any action. If no exact contractual cap exists, the review must verify credible liability containment; without it, a positive Founder decision is blocked. Unresolved evidence or an unmapped risk flag also blocks review readiness. |
| C — prohibited | Borrowing/credit, personal guarantee or surety, asset pledge, custom intentionally uncapped liability, material downside without credible containment, deceptive/unlawful conduct, or policy bypass. | Do not route as an ordinary approval request; no individual Founder experiment approval can waive this class. |

An unknown risk flag fails closed as Class B and cannot reach Founder review until the policy classifies it. A Class C flag takes precedence over Class B flags.

## Numeric-limit placement and rationale

The one-transaction, one-offer, and one-channel Class A controls are structural limits for this narrowly bounded experiment path; they prevent an approval for a pilot from silently becoming repeated or multi-channel activity. All monetary value, plausible-loss estimate, cash spend, Founder attention, delivery labor, and duration limits remain specific to the named experiment and must be written into its approval record. The plausible-loss estimate must disclose evidence and residual risk; it is not a contractual liability cap. No new universal dollar threshold is proposed.

The existing `$50` autonomous single-action and `$200` autonomous single-experiment limits remain unchanged. They are cash-spend controls, not a measure or cap for contract indemnity, refunds, chargebacks, account recovery, or other non-cash exposure. A cash budget of `$0` therefore does not itself make a platform contract bounded.

## Deterministic implementation

`policy_engine.assess_exposure(ExposureRequest)` validates required evidence references, finite numeric caps and a finite estimated maximum plausible loss, transaction/channel/offer counts, required control booleans, and the closed risk-flag vocabulary. The exact contractual liability cap may be `None` for Class A; Class A still requires standardized terms and verified operational containment. The plausible-loss estimate is an evidence-backed review input, not a legal ceiling. Known Class B risks need a complete review card plus a reviewer role, review-evidence reference, and strict `independent_review_complete is True` attestation before they are eligible for Founder review. If a Class B request has no exact contractual cap, it also requires `liability_containment_verified is True`; custom uncapped liability/no credible containment remains Class C. Class C returns prohibited.

`ExposureAssessment.execution_authorized` is always `false`. `policy_engine.evaluate_action()` requires Founder review for real-world experiment actions, standard-term/contract acceptance, account/KYC/listing, customer contact, payment, delivery, and ad purchases; prohibited actions are denied and unregistered action names fail closed. Non-finite spending inputs are rejected. Because no trusted action-to-tool binding exists, the self-reported `internal_reversible_operation` label is also denied (`trusted_action_binding_unavailable`); the evaluator has no `allowed=True` path until such a binding is implemented.

The code cannot authenticate a terms file, independent-review identity, or Founder decision. In particular, the review booleans are routing inputs, not proof. The current repository has no trusted Founder-approval recorder/verifier or action-to-tool binding connected to an execution gateway. Until those integrations exist, external actions remain blocked even if a proposal is review-ready.

## Illustrative applications (not platform-term verification)

- **Upwork Project Catalog:** ordinary standard-form terms do not automatically make a one-order offer Class A. Material indemnity and chargeback/recovery uncertainty route it to Class B; an unclear entity or payout path is also a Class B flag. Any custom uncapped term or lack of credible containment would make it Class C. See the existing CEO-004 approval request and downside review for the evidence and limitations; this proposal does not refresh or expand those platform facts.
- **Stripe or another payment processor:** a one-off transaction under reviewed standard terms may be considered Class A only if the approved transaction/spend caps, dispute response, and containment are credible. Material reserve, reversal, indemnity, or data obligations require Class B review. Custom uncapped liability or no credible containment is Class C. This is a rubric example, not a statement about current Stripe terms or account eligibility.
- **SaaS subscription:** a recurring paid commitment fails the Class A conditions and routes to Class B review and Founder approval. A genuinely one-time, non-renewing purchase may be considered for Class A if all other conditions are evidenced. Do not rely on cancellation language without reviewing the actual terms and renewal settings.
- **Cloud or API provider:** a small use case may be Class A only with verified usage limits, an enforceable per-experiment spend cap, stop/kill conditions, and no disallowed data. Unverified billing exposure or sensitive-data terms route to Class B; material spend without credible containment is Class C. This is not a claim about a named provider's current billing controls.
- **Direct customer contract:** a narrow one-off service on reviewed standard terms may be considered Class A when scope, price, data boundaries, revision limit, and dispute/stop path are explicit. Material indemnity, IP, privacy, refund, or scope ambiguity requires Class B review. Intentionally uncapped custom liability, personal guarantees, or no credible containment is Class C.

## Founder-only judgment points

The Founder must decide whether each proposed transaction-value and loss envelope is genuinely small relative to available cash/reserves; whether the residual contractual and operational downside is acceptable; whether the contracting party, operator, payout path, and legal/tax position are sufficiently clear; and whether to approve the exact offer, channel, cap, timebox, and stop conditions. Those are not decisions made by the classifier or an agent's confidence score.

## CEO-004 migration review — independent Auditor finding

- **Classification:** Class B on the current record, not Class C solely because the public terms lack an exact aggregate-liability ceiling. The downside review documents material indemnity, chargeback/recovery, refund/dispute and surviving-obligation exposure; contracting entity, actual account terms, and payout path also remain unresolved. If qualified review finds no credible containment, or identifies custom uncapped liability, the candidate must be escalated to prohibited Class C.
- **Independent review gate:** The existing `evidence/CEO-004-project-catalog-downside-review-2026-09-25.md` is useful independent risk analysis and supports HOLD/NO-GO, but it is not a domain-appropriate legal review. Its §§Finding and Residual unknowns say the indemnity's enforceability/scope needs qualified legal review and no finite aggregate ceiling was established. Therefore the current record is not eligible for a positive Class B experiment decision: no qualified reviewer role/evidence record resolves these issues. A Founder may still be asked to choose HOLD/NO-GO, return for a separately scoped legal-review request, or decline the candidate; those are not execution approvals.
- **Record discrepancy to reconcile in the CEO-004 branch:** the downside review's §Finding and §Test of the proposed mitigations say no maximum order price was supplied or approved. The later `approvals/CEO-004-approval-request-2026-09-25.md` §§Price and economics and Execution envelope specify one $100 order and one maximum order. Use $100 as the proposed transaction-price cap, not as a cap on chargeback recovery, indemnity, arbitration, account recovery, or aggregate liability. It is not payment evidence. The original review should be corrected or explicitly superseded.
- **If reconsidered:** require a qualified, independent contract/legal review with reviewer role, evidence reference, findings and residual-risk assessment; document finite per-experiment transaction/spend/attention/labor/time caps and an evidence-backed plausible-loss estimate; reconcile the $100/$0/one-order controls; then request a separate written Founder decision for the exact offer/channel before any first live transaction. If no credible containment can be shown, Class C is prohibited.
- **Execution status:** `PENDING_FOUNDER_DECISION — NO-GO FOR EXECUTION`; design only, $0 authorized. No account, KYC, listing, outreach, payment setup, buyer-data collection, payment, or delivery is authorized. See the CEO-004 request §§Decision requested, Founder actions required, and Authority requested, plus the Upwork channel review §Decision.

No classification or review-readiness result is Founder approval. The classifier's `execution_authorized` remains false.
## Files changed in this proposal

- `constitution/constraints.md`
- `constitution/approval-policy.yaml`
- `constitution/authority.md`
- `permissions/spending-policy.yaml`
- `permissions/role-policy.yaml`
- `system/experiment-model.md`
- `policy_engine/engine.py`
- `policy_engine/exposure.py`
- `policy_engine/__init__.py`
- `tools/tool-policy.md`
- `agents/allocator/AGENTS.md`
- `agents/auditor/AGENTS.md`
- `tests/test_policy_engine.py`
- `tests/test_exposure_policy.py`

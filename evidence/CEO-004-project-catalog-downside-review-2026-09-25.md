# Auditor-side downside and stop-safety review

- Review date: 2026-09-25
- Decision: **NO-GO** for a Project Catalog listing, order, payment setup, or delivery under the stated constraints.
- Scope: public Upwork materials only; no account or credential access, account creation, KYC, listing, outreach, payment, or customer data was used.
- Assumption: the future Project Catalog purchase would be a standard marketplace fixed-price Service Contract; no DC account or checkout exists to verify the actual click-through terms.[unverified]

## Finding

The proposed controls bound planned activity, not total downside.[unverified] One order is only a transaction-count cap; no maximum order price is supplied or approved, so it is not yet a dollar cap.[unverified] Upwork’s User Agreement v8.2 and Fixed-Price Escrow Instructions v4.9 are effective July 20, 2026.[1]

## Rules that materially affect the loss boundary

1. **Chargeback/account recovery.** The User Agreement says the User must reimburse Upwork if it receives a chargeback from a payment method used by the User or Client, even where Upwork supplied its services.[1] Upwork may charge accounts, offset amounts owed, deduct from future payments or withdrawals, charge a Payment Method, or use other lawful means to recover amounts.[1] Upwork also says it is not liable for a Client’s default and may reverse Freelancer Fees when the Client defaults or initiates a chargeback.[1] The terms reviewed do not state a finite aggregate dollar cap or recovery time limit for this reimbursement clause.[unverified]

2. **Escrow/refunds are not finality.** Under the standard fixed-price flow, Upwork holds the funded amount in escrow; client approval or no action for 14 calendar days can trigger release, followed by a five-day security hold.[1] A Client may request a refund within 365 days, but approval is at the Freelancer/agency’s discretion.[2] Upwork Support dispute assistance for released payments is limited to the prior 30 days, or remains available while fixed-price funds are still in escrow.[2] A refund request and a chargeback are separate paths.[1][2]

3. **Fixed-price dispute limits are narrow and may cost more than the order.** In Upwork’s fixed-price arbitration process, the amount at issue is limited to funds still held plus funds previously released on that contract.[1] For claims under $20,000, arbitration costs $337.50 per party; one side may pay the full $675 if the other side does not participate.[1] The arbitrator may shift the prevailing party’s arbitration costs to the non-prevailing party in that case, and an optional live hearing has a separate $450 fee.[1] If neither party pays for arbitration in an escrow dispute, the held escrow is released to the Client; for released funds the Upwork dispute ticket closes, while parties may pursue legal action outside the process.[1] This procedure’s contract-value limit does not expressly cap separate chargeback reimbursement or User Agreement indemnity obligations.[1]

4. **Project Catalog early stop.** If a Client does not provide mandatory requirements within 48 hours, Upwork automatically cancels and refunds the Client.[3] A Freelancer can cancel within 24 hours after receiving the Client’s requirements; Upwork says it will refund the Client and there will be no negative consequences during that window.[5] Cancellation remains possible after that window, but Upwork says the Client receives a full refund and the Freelancer’s Job Success Score may be affected.[5] These are early exits, not a cap on liability after work starts.[unverified]

5. **Indemnity/termination.** The User Agreement indemnity covers claims and costs relating to platform use, Work Product, Service Contracts, legal compliance, negligence, and third-party rights, without an express dollar cap in that section.[1] The Agreement’s stated liability cap is for Upwork’s liability to a User, not an express cap on the User’s indemnity or reimbursement obligations.[1] The Agreement says indemnification, fees, and reimbursements survive termination, so account closure or stopping work does not itself erase prior obligations.[1] Public-only research reduces private-data exposure but does not remove work-product/IP, factual-accuracy, or contract-performance risk.[1][unverified]

## Test of the proposed mitigations

| Proposed control | What it bounds | What remains unbounded or unverified |
|---|---|---|
| One transaction | Number of orders, if enforced | No approved maximum package price is stated; add-ons/fees and post-order recovery are not capped by the order count.[unverified] |
| Three agent-hours | Planned research/production effort | Not dispute correspondence, revisions, deadline monitoring, legal response, or duties surviving delivery/termination.[unverified] |
| $0 cash spend | Intended pre-sale spending | Not a guarantee against account/Payment Method recovery; pursuing arbitration requires $337.50 per party for claims under $20,000.[1] |
| No private/personal/financial data | Reduces data-handling/privacy exposure | Does not cap indemnity, third-party-rights, factual-accuracy, or contract claims.[1][unverified] |
| Founder-only KYC | Keeps identity documents away from worker agents, if followed | Does not cap financial liability or establish a corporate liability shield.[unverified] Upwork may request legal name, birth date, address, and SSN/tax ID; no account exists to verify the contracting User, entity, or actual terms.[4][unverified] |

## Decision and residual unknowns

**NO-GO.** Do not list, accept an order, configure payment, or deliver under the current authorization.[unverified] These controls do not satisfy the company requirement for a bounded maximum liability.[unverified] Workers cannot accept an uncapped-liability exception.[unverified]

Exact unresolved items:

- A binding maximum order price, including tiers/add-ons, is not supplied or approved.[unverified]
- The legal account holder/contracting User (individual versus entity), account-specific agreement, account eligibility, KYC/tax status, withdrawal path, and any account-level loss limit are unknown.[unverified]
- Upwork’s public terms do not state a finite aggregate maximum for chargeback reimbursement or its recovery-related costs, nor a verified maximum time window or account-specific reversal limit; actual issuer/processor amounts and appeal outcomes are unknown.[unverified]
- No enforceable client-facing aggregate damages cap or insurance coverage has been verified; the enforceability and scope of platform indemnity require qualified legal review.[unverified]
- The treatment of future Project Catalog-specific terms, revisions, cancellation, and add-ons in the actual checkout/account flow remains unverified.[unverified]

Reconsider only if an authorized review establishes a legally reviewed aggregate loss ceiling that covers platform recovery, indemnity, and client claims, and a separate approval expressly permits the resulting spend and account exposure.[unverified] This review is not launch approval.[unverified]

## Sources

[1] https://www.upwork.com/legal — Upwork Legal Center — User Agreement and Fixed-Price Escrow Instructions
    > "we receive any chargeback from the Payment Method used by you or your Client"
    > "deduct amounts from future payments or withdrawals"
[2] https://support.upwork.com/hc/en-us/articles/17976486850451--Request-a-refund — Upwork Help — Request a refund
    > "within the past 365 days, though approval is at the freelancer’s discretion"
    > "within the previous 30 days"
[3] https://support.upwork.com/hc/en-us/articles/4407894806547-How-to-set-and-manage-project-requirements — Upwork Help — Project Catalog requirements
    > "automatically cancel the project and refund the client’s money"
[4] https://support.upwork.com/hc/en-us/articles/211067818-Know-Your-Customer-KYC-identity-information — Upwork Help — KYC identity information
    > "legal name, birthday, address, and Social Security or tax identification number"
[5] https://support.upwork.com/hc/en-us/articles/4407516715411-How-to-cancel-a-project-in-Project-Catalog-as-a-freelancer — Upwork Help — How to cancel a Project Catalog project as a freelancer
    > "You can cancel a project within 24 hours of receiving a client’s requirements for any reason"

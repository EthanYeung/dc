# CEO-004 — Upwork Project Catalog Channel & Transaction-Path Review

- **Reviewed:** 2026-09-25
- **Scope:** Public Upwork rules plus existing CEO-003 evidence; Upwork Project Catalog is the single candidate channel reviewed.
- **Authority:** Design/review only under CEO-004 Issue #5. No account creation, KYC, listing, outreach, payment setup, buyer-data collection, payment collection, or delivery was attempted.
- **Recommendation:** **Conditional design-only candidate; NO-GO for live execution on this record.**
  A generic fixed-price Catalog purchase and payout path exists, but the specific offer/category and free-listing path remain unverified.[1][2]
  The authorized account operator and account eligibility/KYC are unknown.[10][11]
  The generic U.S. bank withdrawal route has published timing/name requirements, but no DC account or payout method exists to verify.[16][17]
  The linked Auditor downside review found no verified finite aggregate ceiling for chargeback recovery/indemnity; current controls therefore do not meet the company's bounded-loss constraint.[15]
  Retain only as a design question if an authorized legal review can establish a binding acceptable loss ceiling; otherwise reject the channel. This is not launch approval.

## 1. Listing and platform-permission review

Project Catalog supports seller-defined, fixed-scope service listings with a project title/category, description, package/pricing details, work samples, delivery details, and client requirements.[1]
Upwork permits up to 20 active Catalog projects per freelancer account.[1]
Project submissions are reviewed before activation; Upwork says Top Rated, Top Rated Plus, and Expert-Vetted freelancers typically receive review within two business days, while others may wait a few weeks.[2]
Approval or timing is not guaranteed for a future DC project.[2]
If accepted, the project is switched on automatically; therefore review approval—not merely drafting—is a required platform gate.[1][2]

A custom, public-source research service appears **format-compatible** with the Catalog model, but this is an inference, not an approval.[1][2]
The selected category must reflect a service the seller can actually offer; the exact category/subcategory for either prior offer has not been verified.[2]
Upwork screens listing sections for personal contact/payment information and terms compliance; pre-contract communications and payments must remain on Upwork.[3][29]
If a future design uses generative AI, Upwork recommends telling clients up front and respecting any client restriction.[18]
The current User Agreement also licenses platform User Content, including Work Product, for AI personalization unless the account opts out.[15] Before any marketplace content is shared, verify the account's AI preference and rights in all third-party material; no such account preference was checked. Keep any offer limited to public sources and do not request buyer/customer personal data or private financial/customer records.
Any later questionnaire should be limited to the business question and public-source URLs; it must not ask for buyer/customer personal data or private financial/customer records. This is a DC experiment constraint, not evidence of what any buyer will submit.

A Freelancer Basic plan is described as free.[19] The public materials reviewed do **not** expressly confirm that this Catalog listing is available to every Basic account with no separate publish fee or Connects requirement; “$0 Catalog listing” remains unverified.[1][19]

## 2. Fees and buyer checkout

- **Seller fee:** Upwork's published freelancer service-fee range is 0%–15% per contract; the actual DC rate is unknown because there is no account or contract.[6]
- **Buyer-side friction:** The Contract Initiation Fee is $0.99–$14.99.[7]
Official sources conflict on the Client Marketplace Fee: the pricing page's plan table states Basic 3% or 5% and Business Plus 10% or 8% for qualifying U.S. checking-account payers, while its FAQ and the Help article also state Basic fees up to 7.99%.[8][38]
Treat buyer fees as account/checkout-specific; the Catalog price is not necessarily the buyer's all-in price.[7][8][38]
Upwork's Help article says the initiation fee is returned if the fixed-price milestone is not released, but is not refunded after payment to the freelancer even if the freelancer issues a refund; its pricing page labels the fee non-refundable.[7][38]
The Client Marketplace Fee may also be non-refundable after reversal/refund, creating additional buyer friction.[8]

Project Catalog gives clients a browse-and-buy path that does not require posting a job and selecting from proposals.[4][5]
The buyer path is: discover/compare a Catalog project; choose a service tier and any add-ons; provide a billing method and confirm/fund the purchase; submit requested requirements; then use the Upwork contract/workroom for communication and delivery.[4][5]
The buyer has 48 hours to submit requirements or the project is automatically canceled and refunded.[4]
A client may also cancel within the first 24 hours for a full refund.[32]
Listing visibility, category placement, seller reputation, and buyer conversion for DC have not been observed.

## 3. Transaction-to-cash path and blockers

1. **Approval/listing:** Submit the project and wait for review.[1]
For sellers outside the Top Rated, Top Rated Plus, or Expert-Vetted groups, Upwork says review may take a few weeks due to submission volume.[2]
2. **Purchase/funding:** A buyer purchases a fixed-price Catalog project and submits requirements.[4]
The purchase/order balance is not DC cash.[12][27]
3. **Delivery/review:** After the seller submits work, the client has 14 days to approve or request changes; approved or auto-released funds then enter a five-day security hold before becoming available to withdraw.[12]
A change request, refund request, dispute, or payment reversal can delay or defeat realization.[12][13][14]
4. **Withdrawal:** Upwork requires tax information before setting up a withdrawal method.[27]
For Direct to U.S. Bank, Upwork lists an eligible U.S. bank account that accepts ACH, two-to-five business days for deposit, a three-day activation delay for a newly confirmed withdrawal method, and a bank-account name that must match the verified Upwork name.[16][17]
The published method is fee-free for a U.S. tax address; Upwork lists a $2.99 withdrawal fee for a non-U.S. tax address, effective September 1, 2026.[16]
Upwork's available payout methods may vary and change over time; the options are account/location-specific and appear during setup, which has not occurred.[27]
Upwork says temporary holds or suspensions must be resolved before earnings can be withdrawn.[37] The current User Agreement v8.2 (effective July 20, 2026) also reserves power to hold or refuse disbursement pending tax/identity information, dispute/chargeback risk, suspected fraud, performance insecurity, or an investigation; the specific release conditions and timing for a DC account are unknown.[15]
5. **Realized cash:** Only the net amount actually deposited to an eligible, matching bank account counts as cash.[16][17]
Escrow, “Pending,” and an Upwork balance are not realized cash.[12][27]

No DC tax profile, verified name, ACH-capable bank, withdrawal method, or account-specific payout timing/fee has been checked.
The generic platform path exists; the DC path to bank cash does not yet.[16][17][27]

## 4. Refunds, disputes, chargebacks, and loss cap

Upwork's freelancer refund tool limits a direct refund to the lower of available account funds and the relevant net contract transactions from the preceding 180 days; its help page points sellers to Support for certain 180–365-day cases.[13]
A fixed-price refund page describes a client request within 180 days, while a general refund page describes requests up to 365 days with seller discretion.[24][25]
The published help paths are not fully aligned on the route after 180 days, so the refund horizon is not a clean risk cap.[24][25]

Upwork says chargeback outcomes are determined by the financial institution and that Payment Protection applies only when its eligibility conditions are met; protection is not guaranteed in every case.[14][31]
The current User Agreement permits Upwork to seek chargeback reimbursement by offsetting future payments/withdrawals, charging a Payment Method, or using other lawful recovery means.[15]
Therefore the five-day hold is not a chargeback finality guarantee, and no firm per-project maximum loss is established by the sources reviewed.[12][15]
At minimum, a pilot could lose the entire paid amount after delivery; labor/time and any further recovery or refund exposure also matter. [unverified]

For a later, separately approved pilot, Upwork lets sellers set a maximum number of simultaneous Catalog orders; if left unset, the default is 20.[33] A design should set the limit to one and pause the listing after the first order, if the account controls permit, to bound concurrency—not to eliminate refund or chargeback exposure.[33]

## 5. Competition and prior-evidence fit

Upwork says Project Catalog contains more than 290,000 projects platform-wide.[5] This is a broad supply/competition signal, not a count of direct competitors for a public-source research brief or bookkeeping workflow diagnostic.

The prior CEO-003 public demand scan recorded:

- R2, posted September 3, 2026, was a $100 fixed-price research job; the CEO-003 September 25 snapshot recorded 10–15 proposals and one hire.[34]
Its description asks for broad expert-level market, industry, competitor, and business research, not a short packaged brief.[34]
- R1, posted September 15, 2026, is a $1,200/month market-research/data-entry role; the CEO-003 September 25 snapshot recorded 20–50 proposals and six hires.[35]
The prior CEO-003 snapshot treated R1 as a privacy/workload mismatch, not a suitable low-data-risk offer.[35][unverified]

These prior CEO-003 observations are public job-post competition/activity signals, not Project Catalog category saturation, verified payment receipts, demand for DC, or a Catalog sale.[34][35]
The underlying offer is also unresolved: CEO-003's cash-mechanism record describes a bookkeeping month-end-close diagnostic with a $149 unvalidated price hypothesis, while the demand scan proposes a public-source competitor brief at $50–$100.[unverified]
Those are different offers, buyers, requirements, and likely categories. Do not draft a live listing until one is selected and scoped. [unverified]

Prior evidence and the original public posts are in `evidence/CEO-003-public-demand-scan-2026-09-25.md` §2 (R1/R2) and its Sources list.[34][35] The prior candidate/authority decision is in `evidence/CEO-003-cash-mechanism-decision-2026-09-24.md` §§5–6. [unverified]

## 6. Account, identity, eligibility, and unresolved gates

Upwork's general rules include age, location, work-authorization, and identity/account-integrity requirements.[10][26]
KYC may request a legal name, date of birth, address, and Social Security or tax identification number.[11]
Upwork prohibits another person from logging into an account or working/communicating through it on the account holder's behalf.[26]
For company use, each individual needs their own account/login; a Founder credential cannot be delegated to an agent.[26] The authorized freelancer/agency operator and DC's legal/tax identity, eligibility, and ability to operate the profile compliantly are unknown. [unverified]
This is not permission for an agent to use a founder's credentials.[26]
No identity or tax data was requested, accessed, or stored.

**Open gates before any Founder decision to authorize a real test:**

1. Select one offer and buyer; reconcile the $149 bookkeeping diagnostic versus the $50–$100 public-source brief. [unverified]
2. Confirm the exact permitted Catalog category/subcategory and whether a free Basic account can publish that listing at $0 without a paid feature or Connects.[2][19]
3. Identify the eligible, authorized freelancer/agency operator and account form; each user must use their own authorized login, and the actual account holder must complete any KYC/tax/bank steps directly.[10][11][26]
4. Verify the account-specific seller fee, buyer checkout total, U.S. tax-address status, ACH eligibility, bank-name match, and actual withdrawal route.[6][8][16]
5. Define order/price/time limits and a Founder-accepted maximum refund/chargeback loss. Public sources do not establish a firm maximum.[14][15]
6. Use requirements limited to the business question and public URLs; do not request or collect buyer personal data or client/customer/financial records. If AI is used, disclose it and honor client restrictions.[3][18][29]

## Decision

**Conditionally propose Upwork Project Catalog only as a design-stage candidate; do not approve it as an executable channel.**[1][2]
It has an official fixed-price catalog and payout mechanism, but is rented distribution, has substantial platform-wide supply, is weakly matched to the prior demand sample, and is not verified for DC's listing/account/cash path.[1][5][34]
The Auditor downside review separately found no verified binding ceiling for total liability under current public terms.[15]
Reject if the exact category or zero-upfront-cost listing path cannot be verified.[2][19]
Reject if an authorized operator/account eligibility or payout path is not established.[10][11][16]
Reject if a legally acceptable loss cap cannot be verified and accepted.[15]

**Execution status remains unchanged:** $0 capital and no active experiment; no account/KYC/listing/outreach/payment setup/customer-data collection/payment/delivery was attempted. No buyer PII was captured in this review.

## Sources

[1] https://support.upwork.com/hc/en-us/articles/360057397533-How-to-create-a-project-in-Project-Catalog
[2] https://support.upwork.com/hc/en-us/articles/4408644453395-How-we-review-your-Project-Catalog-project
[3] https://support.upwork.com/hc/en-us/articles/360058122033-How-to-build-your-best-project-in-Project-Catalog
[4] https://support.upwork.com/hc/en-us/articles/4407886651283-How-to-purchase-a-project-in-Project-Catalog
[5] https://support.upwork.com/hc/en-us/articles/10408677826963-What-is-Project-Catalog-on-Upwork
[6] https://support.upwork.com/hc/en-us/articles/211062538-Learn-about-the-Freelancer-Service-Fee
[7] https://support.upwork.com/hc/en-us/articles/26106318334611-What-is-the-Contract-Initiation-Fee-on-Upwork
[8] https://support.upwork.com/hc/en-us/articles/4660220468499-What-is-the-Client-Marketplace-Fee
[10] https://support.upwork.com/hc/en-us/articles/211067778-Who-s-eligible-to-join-and-use-Upwork
[11] https://support.upwork.com/hc/en-us/articles/211067818-Know-Your-Customer-KYC-identity-information
[12] https://support.upwork.com/hc/en-us/articles/211063718-How-payments-for-milestones-and-fixed-price-contracts-work
[13] https://support.upwork.com/hc/en-us/articles/211068538-How-to-give-a-refund-to-your-client
[14] https://support.upwork.com/hc/en-us/articles/14084991625107-What-happens-when-your-client-files-a-chargeback
[15] https://www.upwork.com/legal
[16] https://support.upwork.com/hc/en-us/articles/227022468-Direct-to-U-S-Bank-timing-and-fees-explained
[17] https://support.upwork.com/hc/en-us/articles/211063818-How-to-withdraw-earnings-to-your-U-S-bank-on-Upwork
[18] https://support.upwork.com/hc/en-us/articles/22983791592595-How-to-use-Uma-Upwork-s-Mindful-AI-as-a-freelancer
[19] https://support.upwork.com/hc/en-us/articles/40444316172051-What-s-the-difference-between-Freelancer-Basic-and-Freelancer-Plus
[24] https://support.upwork.com/hc/en-us/articles/40525891840787-The-money-has-already-been-released-can-I-still-get-a-refund
[25] https://support.upwork.com/hc/en-us/articles/17976486850451--Request-a-refund
[26] https://support.upwork.com/hc/en-us/articles/18513114070419-Represent-yourself-authentically
[27] https://support.upwork.com/hc/en-us/articles/211060918-How-to-get-paid-on-Upwork
[29] https://support.upwork.com/hc/en-us/articles/25205969832083-Upwork-Trust-and-Safety
[31] https://support.upwork.com/hc/en-us/articles/211063748-How-Fixed-Price-Payment-Protection-works-for-freelancers-on-Upwork
[32] https://support.upwork.com/hc/en-us/articles/4407886746131-How-to-cancel-a-project-you-purchased-on-Project-Catalog
[33] https://support.upwork.com/hc/en-us/articles/4407886394131-How-to-manage-your-project-in-Project-Catalog
[34] https://www.upwork.com/freelance-jobs/apply/Research-Analyst-Needed-for-Market-Research-Data-Analysis-Business-Insights_~022095554866314635019
[35] https://www.upwork.com/freelance-jobs/apply/Market-Research-Data-Entry-Specialist_~022099781294792555073
[37] https://support.upwork.com/hc/en-us/articles/211063828-How-to-troubleshoot-withdrawal-issues-on-Upwork
[38] https://www.upwork.com/pricing/client

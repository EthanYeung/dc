# Opportunity State Machine

Default states:

DISCOVERED
-> SCREENING
-> AUDIENCE_TEST
-> DISTRIBUTION_BUILD
-> COMMERCIAL_SIGNAL
-> PAID_VALIDATION
-> VENTURE
-> SCALING
-> HARVEST

Any non-terminal state may move to KILLED.

These states are defaults, not mandatory bureaucracy. The allocator may skip a stage when stronger external evidence already exists, but the reason and supporting evidence must be recorded.

## State meanings

### DISCOVERED
A candidate problem/customer/business-model combination has been identified.

### SCREENING
The company checks whether the problem is real, the target user is economically relevant, the AI-native operating advantage is plausible, and the legal/operational surface is acceptable.

### AUDIENCE_TEST
Test whether the target users can be reached or attracted at acceptable cost and with sufficient intent.

### DISTRIBUTION_BUILD
Invest in a repeatable acquisition or utility channel that can compound into a durable user relationship or other distribution asset.

### COMMERCIAL_SIGNAL
Measure whether the audience demonstrates behavior plausibly connected to willingness to pay: repeat use, qualified inquiry, saved work, demo request, high-intent feature use, waitlist, pricing interaction, or comparable costly signal.

### PAID_VALIDATION
Obtain verified economic evidence such as payment, deposit or another legitimate commercial commitment.

### VENTURE
A validated opportunity receives an operating model, product/service scope and ongoing capital allocation.

### SCALING
Increase capital only after acquisition, retention, gross margin and operating burden show credible repeatability.

### HARVEST
Optimize cash generation, efficiency and asset extraction while limiting unnecessary reinvestment.

## Gate principle

Capital release must increase with evidence quality.

A transition requires:
- explicit evidence;
- known remaining uncertainty;
- a defined target user;
- a unit of economic or strategic value;
- bounded next-step budget;
- stop condition;
- where relevant, a plausible distribution mechanism.

An attractive narrative, large TAM, high traffic volume or agent confidence is not a transition criterion.

## Distribution guardrail

Distribution is an asset only when at least one of the following becomes measurable:
- qualified audience;
- repeat use;
- permissioned direct relationship;
- low-cost recurring acquisition;
- proprietary demand or behavior data;
- commercial intent.

Generic traffic without target-customer fit is not a valuable company asset.

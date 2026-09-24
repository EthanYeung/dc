# Opportunity State Machine

States:

DISCOVERED -> SCREENING -> VALIDATING -> PAID_VALIDATION -> VENTURE -> SCALING -> HARVEST

Any non-terminal state may move to KILLED.

## Gate principle

Capital release must increase with evidence quality.

A transition requires:
- explicit evidence;
- known remaining uncertainty;
- unit of economic value;
- bounded next-step budget;
- stop condition.

An attractive narrative is not a transition criterion.

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionRequest:
    role: str
    action: str
    spend_usd: float = 0.0
    recurring_commitment_usd: float = 0.0
    irreversible: bool = False
    destructive_production: bool = False
    credential_scope_expansion: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    founder_approval_required: bool
    reason: str


PROHIBITED_ACTIONS = {
    "bypass_policy_engine",
    "disable_audit_logging",
    "disable_kill_switch",
    "store_plaintext_secrets_in_git",
    "fabricate_evidence",
}

AUTONOMOUS_SINGLE_ACTION_LIMIT_USD = 50.0
AUTONOMOUS_RECURRING_COMMITMENT_LIMIT_USD = 0.0


def evaluate_action(request: ActionRequest) -> PolicyDecision:
    """Fail closed on known high-risk actions.

    Economic judgment belongs to agents; hard limits belong to deterministic code.
    """
    if request.spend_usd < 0 or request.recurring_commitment_usd < 0:
        return PolicyDecision(False, False, "invalid_negative_amount")

    if request.action in PROHIBITED_ACTIONS:
        return PolicyDecision(False, False, "prohibited_action")

    if request.credential_scope_expansion:
        return PolicyDecision(False, True, "credential_scope_expansion")

    if request.destructive_production:
        return PolicyDecision(False, True, "destructive_production_action")

    if request.irreversible:
        return PolicyDecision(False, True, "irreversible_external_commitment")

    if request.recurring_commitment_usd > AUTONOMOUS_RECURRING_COMMITMENT_LIMIT_USD:
        return PolicyDecision(False, True, "new_recurring_commitment")

    if request.spend_usd > AUTONOMOUS_SINGLE_ACTION_LIMIT_USD:
        return PolicyDecision(False, True, "spend_above_autonomous_limit")

    return PolicyDecision(True, False, "within_autonomous_policy")

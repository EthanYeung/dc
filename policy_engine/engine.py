import math
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
    "borrow",
    "take_credit",
    "personal_guarantee",
    "pledge_assets",
    "accept_custom_uncapped_liability",
}

TRUSTED_ACTION_BINDING_REQUIRED = {"internal_reversible_operation"}

FOUNDER_APPROVAL_ACTIONS = {
    "buy_ads",
    "accept_standardized_platform_terms",
    "accept_contract_terms",
    "create_marketplace_account",
    "complete_kyc",
    "publish_listing",
    "contact_customer",
    "accept_payment",
    "deliver_paid_experiment",
    "record_payout_state",
    "start_real_world_experiment",
}

AUTONOMOUS_SINGLE_ACTION_LIMIT_USD = 50.0
AUTONOMOUS_RECURRING_COMMITMENT_LIMIT_USD = 0.0


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def evaluate_action(request: ActionRequest) -> PolicyDecision:
    """Fail closed; self-reported action labels never authorize execution.

    Economic judgment belongs to agents; hard limits belong to deterministic code.
    Until a trusted action-to-tool binding exists, candidate autonomous actions
    remain blocked.
    """
    if not _is_finite_number(request.spend_usd) or not _is_finite_number(
        request.recurring_commitment_usd
    ):
        return PolicyDecision(False, False, "invalid_amount")

    if request.spend_usd < 0 or request.recurring_commitment_usd < 0:
        return PolicyDecision(False, False, "invalid_negative_amount")

    if request.action in PROHIBITED_ACTIONS:
        return PolicyDecision(False, False, "prohibited_action")

    if request.action in TRUSTED_ACTION_BINDING_REQUIRED:
        return PolicyDecision(False, False, "trusted_action_binding_unavailable")

    if request.action in FOUNDER_APPROVAL_ACTIONS:
        return PolicyDecision(False, True, "founder_approval_required")

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

    return PolicyDecision(False, True, "unregistered_action_requires_review")

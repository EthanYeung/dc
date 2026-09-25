from policy_engine import ActionRequest, evaluate_action


def test_self_asserted_internal_action_label_does_not_grant_permission():
    d = evaluate_action(
        ActionRequest(
            role="growth", action="internal_reversible_operation", spend_usd=20
        )
    )
    assert d.allowed is False
    assert d.founder_approval_required is False
    assert d.reason == "trusted_action_binding_unavailable"


def test_large_spend_requires_founder_approval():
    d = evaluate_action(ActionRequest(role="allocator", action="buy_ads", spend_usd=51))
    assert d.allowed is False
    assert d.founder_approval_required is True


def test_recurring_commitment_requires_approval():
    d = evaluate_action(
        ActionRequest(
            role="builder",
            action="subscribe_service",
            recurring_commitment_usd=10,
        )
    )
    assert d.allowed is False
    assert d.founder_approval_required is True


def test_prohibited_action_is_denied_not_escalated():
    d = evaluate_action(
        ActionRequest(role="allocator", action="bypass_policy_engine")
    )
    assert d.allowed is False
    assert d.founder_approval_required is False


def test_accepting_standardized_platform_terms_requires_founder_approval():
    d = evaluate_action(
        ActionRequest(
            role="growth",
            action="accept_standardized_platform_terms",
            spend_usd=0,
        )
    )
    assert d.allowed is False
    assert d.founder_approval_required is True
    assert d.reason == "founder_approval_required"


def test_unregistered_action_fails_closed():
    d = evaluate_action(
        ActionRequest(role="growth", action="unregistered_external_action")
    )
    assert d.allowed is False
    assert d.founder_approval_required is True
    assert d.reason == "unregistered_action_requires_review"


def test_borrowing_guarantees_pledges_and_custom_uncapped_terms_are_prohibited():
    prohibited = (
        "borrow",
        "take_credit",
        "personal_guarantee",
        "pledge_assets",
        "accept_custom_uncapped_liability",
    )
    for action in prohibited:
        d = evaluate_action(ActionRequest(role="allocator", action=action))
        assert d.allowed is False
        assert d.founder_approval_required is False
        assert d.reason == "prohibited_action"


def test_non_finite_spend_or_recurring_amount_fails_closed():
    for amount in (float("nan"), float("inf")):
        requests = (
            ActionRequest(
                role="growth",
                action="internal_reversible_operation",
                spend_usd=amount,
            ),
            ActionRequest(
                role="growth",
                action="internal_reversible_operation",
                recurring_commitment_usd=amount,
            ),
        )
        for request in requests:
            d = evaluate_action(request)
            assert d.allowed is False
            assert d.founder_approval_required is False
            assert d.reason == "invalid_amount"


def test_small_ad_purchase_requires_experiment_founder_approval():
    d = evaluate_action(ActionRequest(role="growth", action="buy_ads", spend_usd=1))
    assert d.allowed is False
    assert d.founder_approval_required is True
    assert d.reason == "founder_approval_required"

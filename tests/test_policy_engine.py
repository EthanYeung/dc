from policy_engine import ActionRequest, evaluate_action


def test_small_reversible_action_is_allowed():
    d = evaluate_action(ActionRequest(role="growth", action="approved_test", spend_usd=20))
    assert d.allowed is True
    assert d.founder_approval_required is False


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

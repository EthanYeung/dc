import policy_engine


def _class_a_request(**overrides):
    values = {
        "experiment_id": "GOV-TEST-001",
        "terms_evidence_ref": "evidence/standard-terms.md",
        "standardized_terms": True,
        "contractual_liability_cap_usd": None,
        "max_transactions": 1,
        "max_transaction_value_usd": 100,
        "estimated_max_plausible_loss_usd": 100,
        "max_direct_spend_usd": 0,
        "max_founder_attention_minutes": 30,
        "max_delivery_labor_hours": 3,
        "timebox_days": 30,
        "max_channels": 1,
        "max_offers": 1,
        "no_recurring_commitment": True,
        "no_sensitive_data": True,
        "no_regulated_advice": True,
        "risk_assessment_complete": True,
        "stop_conditions_defined": True,
        "reversal_plan_defined": True,
        "operational_containment_verified": True,
    }
    values.update(overrides)
    return policy_engine.ExposureRequest(**values)


def test_standardized_single_order_without_exact_liability_cap_is_reviewable():
    request_type = getattr(policy_engine, "ExposureRequest", None)
    assess_exposure = getattr(policy_engine, "assess_exposure", None)
    assert request_type is not None and callable(assess_exposure), (
        "exposure assessment API is required before a Founder review can be routed"
    )

    decision = assess_exposure(_class_a_request())

    assert decision.risk_class == "A"
    assert decision.eligible_for_founder_review is True
    assert decision.founder_approval_required is True
    assert decision.execution_authorized is False


def test_unknown_risk_flag_cannot_be_cleared_by_a_generic_review_boolean():
    decision = policy_engine.assess_exposure(
        _class_a_request(
            risk_flags=frozenset({"future_unmapped_flag"}),
            independent_review_complete=True,
        )
    )
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.founder_approval_required is True
    assert decision.execution_authorized is False
    assert decision.reason == "unknown_risk_flag_requires_policy_review"


def test_class_b_material_indemnity_requires_independent_review_and_founder_approval():
    request = _class_a_request(
        risk_flags=frozenset({"material_indemnity"}),
        independent_review_complete=False,
    )
    pending = policy_engine.assess_exposure(request)
    assert pending.risk_class == "B"
    assert pending.eligible_for_founder_review is False
    assert pending.founder_approval_required is True
    assert pending.execution_authorized is False

    reviewed = policy_engine.assess_exposure(
        _class_a_request(
            risk_flags=frozenset({"material_indemnity"}),
            independent_review_complete=True,
            independent_reviewer_role="auditor",
            independent_review_evidence_ref="evidence/independent-review.md",
            liability_containment_verified=True,
        )
    )
    assert reviewed.risk_class == "B"
    assert reviewed.eligible_for_founder_review is True
    assert reviewed.founder_approval_required is True
    assert reviewed.execution_authorized is False


def test_class_c_borrowing_guarantees_pledges_and_uncapped_terms_are_prohibited():
    prohibited_flags = (
        "borrowing",
        "personal_guarantee",
        "asset_pledge",
        "custom_uncapped_liability",
        "no_credible_containment",
        "deception_or_illegality",
        "policy_bypass",
    )
    for flag in prohibited_flags:
        decision = policy_engine.assess_exposure(
            _class_a_request(
                risk_flags=frozenset({flag}),
                independent_review_complete=True,
            )
        )
        assert decision.risk_class == "C"
        assert decision.eligible_for_founder_review is False
        assert decision.founder_approval_required is False
        assert decision.execution_authorized is False
        assert decision.reason == "class_c_prohibited"


def test_malformed_review_identifiers_fail_closed_instead_of_crashing():
    decision = policy_engine.assess_exposure(_class_a_request(experiment_id=42))
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.execution_authorized is False
    assert decision.reason == "class_b_requires_complete_card_and_independent_review"


def test_truthy_strings_do_not_satisfy_required_review_controls():
    decision = policy_engine.assess_exposure(
        _class_a_request(
            risk_assessment_complete="verified",
            stop_conditions_defined="yes",
            reversal_plan_defined="yes",
        )
    )
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.execution_authorized is False


def test_truthy_string_does_not_count_as_independent_review():
    decision = policy_engine.assess_exposure(
        _class_a_request(
            risk_flags=frozenset({"material_indemnity"}),
            independent_review_complete="yes",
        )
    )
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.founder_approval_required is True
    assert decision.execution_authorized is False


def test_malformed_risk_flag_collection_fails_closed():
    decision = policy_engine.assess_exposure(
        _class_a_request(risk_flags="material_indemnity")
    )
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.founder_approval_required is True
    assert decision.execution_authorized is False
    assert decision.reason == "invalid_risk_flags_requires_policy_review"


def test_unrepresentably_large_financial_cap_fails_closed():
    decision = policy_engine.assess_exposure(
        _class_a_request(max_transaction_value_usd=10**400)
    )
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.execution_authorized is False


def test_missing_loss_estimate_blocks_founder_review():
    decision = policy_engine.assess_exposure(
        _class_a_request(estimated_max_plausible_loss_usd=None)
    )
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.founder_approval_required is True
    assert decision.execution_authorized is False


def test_independent_review_boolean_without_identity_and_evidence_is_insufficient():
    decision = policy_engine.assess_exposure(
        _class_a_request(
            risk_flags=frozenset({"material_indemnity"}),
            independent_review_complete=True,
        )
    )
    assert decision.risk_class == "B"
    assert decision.eligible_for_founder_review is False
    assert decision.founder_approval_required is True
    assert decision.execution_authorized is False


def test_class_b_without_exact_cap_needs_verified_liability_containment():
    uncontained = policy_engine.assess_exposure(
        _class_a_request(
            standardized_terms=False,
            risk_flags=frozenset({"nonstandard_terms"}),
            independent_review_complete=True,
            independent_reviewer_role="legal",
            independent_review_evidence_ref="evidence/legal-review.md",
            liability_containment_verified=False,
        )
    )
    assert uncontained.risk_class == "B"
    assert uncontained.eligible_for_founder_review is False
    assert uncontained.founder_approval_required is True
    assert uncontained.execution_authorized is False

    contained = policy_engine.assess_exposure(
        _class_a_request(
            standardized_terms=False,
            risk_flags=frozenset({"nonstandard_terms"}),
            independent_review_complete=True,
            independent_reviewer_role="legal",
            independent_review_evidence_ref="evidence/legal-review.md",
            liability_containment_verified=True,
        )
    )
    assert contained.risk_class == "B"
    assert contained.eligible_for_founder_review is True
    assert contained.founder_approval_required is True
    assert contained.execution_authorized is False

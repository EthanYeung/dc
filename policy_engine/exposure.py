from dataclasses import dataclass, field
import math


CLASS_B_RISK_FLAGS = frozenset(
    {
        "material_indemnity",
        "sensitive_data",
        "regulated_advice",
        "significant_refund_or_dispute_risk",
        "unclear_contracting_entity",
        "legal_or_tax_uncertainty",
        "uncertain_surviving_obligations",
        "recurring_commitment",
        "nonstandard_terms",
        "multiple_transactions",
        "unverified_payout_path",
    }
)
CLASS_C_RISK_FLAGS = frozenset(
    {
        "borrowing",
        "personal_guarantee",
        "asset_pledge",
        "custom_uncapped_liability",
        "no_credible_containment",
        "deception_or_illegality",
        "policy_bypass",
    }
)


@dataclass(frozen=True)
class ExposureRequest:
    """Experiment facts used to decide whether a proposal may go to Founder review.

    This is a review-readiness assessment only. It never grants authority to execute.
    """

    experiment_id: str | None = None
    terms_evidence_ref: str | None = None
    standardized_terms: bool | None = None
    contractual_liability_cap_usd: float | None = None
    max_transactions: int | None = None
    max_transaction_value_usd: float | None = None
    estimated_max_plausible_loss_usd: float | None = None
    max_direct_spend_usd: float | None = None
    max_founder_attention_minutes: float | None = None
    max_delivery_labor_hours: float | None = None
    timebox_days: float | None = None
    max_channels: int | None = None
    max_offers: int | None = None
    no_recurring_commitment: bool | None = None
    no_sensitive_data: bool | None = None
    no_regulated_advice: bool | None = None
    risk_assessment_complete: bool = False
    stop_conditions_defined: bool = False
    reversal_plan_defined: bool = False
    operational_containment_verified: bool = False
    liability_containment_verified: bool | None = None
    independent_review_complete: bool = False
    independent_reviewer_role: str | None = None
    independent_review_evidence_ref: str | None = None
    risk_flags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class ExposureAssessment:
    risk_class: str
    eligible_for_founder_review: bool
    founder_approval_required: bool
    execution_authorized: bool
    reason: str


def _finite_number(value: object, *, allow_zero: bool) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        if not math.isfinite(float(value)):
            return False
    except (OverflowError, TypeError, ValueError):
        return False
    return value >= 0 if allow_zero else value > 0


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _review_card_complete(request: ExposureRequest) -> bool:
    return all(
        (
            _non_empty_text(request.experiment_id),
            _non_empty_text(request.terms_evidence_ref),
            _positive_int(request.max_transactions),
            _finite_number(request.max_transaction_value_usd, allow_zero=False),
            _finite_number(request.estimated_max_plausible_loss_usd, allow_zero=True),
            _finite_number(request.max_direct_spend_usd, allow_zero=True),
            _finite_number(request.max_founder_attention_minutes, allow_zero=True),
            _finite_number(request.max_delivery_labor_hours, allow_zero=True),
            _finite_number(request.timebox_days, allow_zero=False),
            _positive_int(request.max_channels),
            _positive_int(request.max_offers),
            request.risk_assessment_complete is True,
            request.stop_conditions_defined is True,
            request.reversal_plan_defined is True,
        )
    ) and (
        request.contractual_liability_cap_usd is None
        or _finite_number(request.contractual_liability_cap_usd, allow_zero=True)
    )


def assess_exposure(request: ExposureRequest) -> ExposureAssessment:
    """Classify exposure and determine review routing, never execution permission.

    Numeric operating caps are supplied per experiment and reviewed by Founder;
    this function does not invent company-wide dollar or labor thresholds.
    """
    if not isinstance(request.risk_flags, frozenset) or any(
        not isinstance(flag, str) or not flag.strip()
        for flag in request.risk_flags
    ):
        return ExposureAssessment(
            risk_class="B",
            eligible_for_founder_review=False,
            founder_approval_required=True,
            execution_authorized=False,
            reason="invalid_risk_flags_requires_policy_review",
        )

    if request.risk_flags & CLASS_C_RISK_FLAGS:
        return ExposureAssessment(
            risk_class="C",
            eligible_for_founder_review=False,
            founder_approval_required=False,
            execution_authorized=False,
            reason="class_c_prohibited",
        )

    unknown_flags = request.risk_flags - CLASS_B_RISK_FLAGS
    if unknown_flags:
        return ExposureAssessment(
            risk_class="B",
            eligible_for_founder_review=False,
            founder_approval_required=True,
            execution_authorized=False,
            reason="unknown_risk_flag_requires_policy_review",
        )

    review_card_complete = _review_card_complete(request)
    class_a_fit = all(
        (
            request.standardized_terms is True,
            request.max_transactions == 1,
            request.max_channels == 1,
            request.max_offers == 1,
            request.no_recurring_commitment is True,
            request.no_sensitive_data is True,
            request.no_regulated_advice is True,
            request.operational_containment_verified is True,
            not request.risk_flags,
            review_card_complete,
        )
    )
    if class_a_fit:
        return ExposureAssessment(
            risk_class="A",
            eligible_for_founder_review=True,
            founder_approval_required=True,
            execution_authorized=False,
            reason="class_a_ready_for_founder_review",
        )

    independent_review_record_complete = all(
        (
            request.independent_review_complete is True,
            _non_empty_text(request.independent_reviewer_role),
            _non_empty_text(request.independent_review_evidence_ref),
        )
    )
    liability_containment_complete = (
        request.contractual_liability_cap_usd is not None
        or request.liability_containment_verified is True
    )
    eligible_for_founder_review = all(
        (
            review_card_complete,
            independent_review_record_complete,
            liability_containment_complete,
        )
    )
    if not review_card_complete or not independent_review_record_complete:
        reason = "class_b_requires_complete_card_and_independent_review"
    elif not liability_containment_complete:
        reason = "class_b_requires_verified_liability_containment"
    else:
        reason = "class_b_ready_for_founder_review"

    return ExposureAssessment(
        risk_class="B",
        eligible_for_founder_review=eligible_for_founder_review,
        founder_approval_required=True,
        execution_authorized=False,
        reason=reason,
    )

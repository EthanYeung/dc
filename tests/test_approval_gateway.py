import base64
import hashlib
import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from threading import Event, Thread
from types import MappingProxyType
from typing import cast

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import runtime.approval_gateway as approval_gateway_module
from policy_engine.engine import ActionRequest, evaluate_action
from policy_engine.exposure import ExposureRequest
from runtime.approval_gateway import (
    ApprovalRecord,
    ApprovalStore,
    ApprovalVerifier,
    ExecutionGateway,
    ExecutionRequest,
    KillSwitch,
    SimulatedExternalTool,
    ToolBinding,
    ToolBindingRegistry,
    ToolResult,
    TrustedPrincipal,
    _request_digest,
)

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)  # noqa: UP017


def _key_pair():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, public_key


def _exposure_request() -> ExposureRequest:
    return ExposureRequest(
        experiment_id="CEO-004-001",
        terms_evidence_ref="evidence/CEO-004-terms",
        standardized_terms=True,
        contractual_liability_cap_usd=None,
        max_transactions=1,
        max_transaction_value_usd=100.0,
        estimated_max_plausible_loss_usd=100.0,
        max_direct_spend_usd=0.0,
        max_founder_attention_minutes=30.0,
        max_delivery_labor_hours=3.0,
        timebox_days=30.0,
        max_channels=1,
        max_offers=1,
        no_recurring_commitment=True,
        no_sensitive_data=True,
        no_regulated_advice=True,
        risk_assessment_complete=True,
        stop_conditions_defined=True,
        reversal_plan_defined=True,
        operational_containment_verified=True,
        risk_flags=frozenset(),
    )


def _signed_approval(private_key: Ed25519PrivateKey, **overrides) -> ApprovalRecord:
    record = ApprovalRecord(
        approval_id="APR-CEO-004-001",
        experiment_id="CEO-004-001",
        approved_action="publish_listing",
        approved_offer="offer-001",
        approved_channel="upwork-project-catalog",
        risk_class="A",
        exposure=_exposure_request(),
        founder_decision="approved",
        decision_timestamp=NOW,
        expires_at=NOW + timedelta(days=7),
        evidence_refs=("evidence/CEO-004-approval",),
        key_id="founder-test-key",
        signature_b64="",
    )
    record = replace(record, **overrides)
    signature = private_key.sign(record.signing_bytes())
    return replace(record, signature_b64=base64.b64encode(signature).decode("ascii"))


def _make_database(path: Path) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "runtime" / "schema.sql"
    with sqlite3.connect(path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.execute(
            "UPDATE gateway_control SET kill_switch_active = 0 WHERE control_id = ?",
            ("global",),
        )


def _make_gateway(
    database_path,
    public_key,
    simulator,
    action_id="publish_listing",
    kill_switch=None,
    clock=None,
):
    return ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=ApprovalVerifier({"founder-test-key": public_key}),
        bindings=ToolBindingRegistry(
            [
                ToolBinding(
                    action_id=action_id,
                    scope="external",
                    handler=simulator,
                    simulation_only=True,
                    allowed_roles=frozenset({"allocator"}),
                )
            ]
        ),
        clock=clock or (lambda: NOW),
        kill_switch=kill_switch or KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "allocator:test-worker", "allocator", request.worker_run_id
        ),
    )


def _make_internal_gateway(database_path, handler, kill_switch=None):
    return ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=ApprovalVerifier({}),
        bindings=ToolBindingRegistry(
            [
                ToolBinding(
                    action_id="internal.run_tests",
                    scope="internal",
                    handler=handler,
                    simulation_only=True,
                    allowed_roles=frozenset({"builder"}),
                )
            ]
        ),
        clock=lambda: NOW,
        kill_switch=kill_switch or KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "builder:test-worker", "builder", request.worker_run_id
        ),
    )


def _execution_request(approval, **overrides):
    request = {
        "idempotency_key": "request-001",
        "actor_role": "allocator",
        "worker_run_id": "run-001",
        "action_id": approval.approved_action,
        "approval_id": approval.approval_id,
        "experiment_id": approval.experiment_id,
        "offer_id": approval.approved_offer,
        "channel_id": approval.approved_channel,
        "transaction_value_usd": 100.0,
        "direct_spend_usd": 0.0,
        "founder_attention_minutes": 5.0,
        "delivery_labor_hours": 1.0,
        "payload": {"simulated": True},
    }
    request.update(overrides)
    return ExecutionRequest(**request)


def _deeply_nested_payload(depth):
    payload = {"leaf": True}
    for _ in range(depth):
        payload = {"nested": payload}
    return payload


def _assert_denial_record(database_path, idempotency_key, reason):
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT decision, reason FROM execution_attempts WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
    assert row == ("deny", reason)


def test_verified_founder_approval_executes_builtin_stub_and_persists_audit(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    simulator = SimulatedExternalTool(calls)

    outcome = _make_gateway(database_path, public_key, simulator).execute(
        _execution_request(approval)
    )

    assert outcome.allowed is True
    assert outcome.status == "verified"
    assert outcome.result is not None and outcome.result.simulated is True
    assert outcome.attempt_id is not None
    opaque_reference = f"gateway-result:{outcome.attempt_id}"
    assert outcome.result.external_ref == opaque_reference
    assert calls == ["publish_listing"]
    with sqlite3.connect(database_path) as connection:
        attempt = connection.execute(
            "SELECT decision, reason, approval_id FROM execution_attempts "
            "WHERE idempotency_key = ?",
            ("request-001",),
        ).fetchone()
        result = connection.execute(
            "SELECT status, result_json FROM execution_results WHERE attempt_id = ?",
            (outcome.attempt_id,),
        ).fetchone()
    assert attempt == ("allow", "founder_approval_verified", approval.approval_id)
    assert result[0] == "verified"
    assert json.loads(result[1])["external_ref"] == opaque_reference


def test_invalid_approval_signature_is_denied_and_audited(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    tampered = replace(approval, signature_b64=base64.b64encode(b"x" * 64).decode("ascii"))
    ApprovalStore(database_path).add_approval(tampered)
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        _execution_request(approval)
    )

    assert outcome.allowed is False
    assert outcome.reason == "invalid_approval_signature"
    assert calls == []
    _assert_denial_record(database_path, "request-001", "invalid_approval_signature")


def test_signed_record_contains_issue_required_scope_and_caps():
    private_key, _ = _key_pair()
    approval = _signed_approval(private_key)
    payload = json.loads(approval.signing_bytes())

    assert payload["approval_id"] == "APR-CEO-004-001"
    assert payload["experiment_id"] == "CEO-004-001"
    assert payload["approved_action"] == "publish_listing"
    assert payload["approved_offer"] == "offer-001"
    assert payload["approved_channel"] == "upwork-project-catalog"
    assert payload["risk_class"] == "A"
    assert payload["max_transactions"] == 1
    assert payload["max_transaction_value_usd"] == 100.0
    assert payload["max_direct_spend_usd"] == 0.0
    assert payload["max_founder_attention_minutes"] == 30.0
    assert payload["max_delivery_labor_hours"] == 3.0
    assert payload["expires_at"].endswith("Z")
    assert payload["decision_timestamp"].endswith("Z")
    assert payload["evidence_refs"] == ["evidence/CEO-004-approval"]


def test_registered_internal_action_runs_without_founder_approval(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    outcome = _make_internal_gateway(database_path, internal_tool).execute(
        ExecutionRequest(
            idempotency_key="internal-run-001",
            actor_role="builder",
            worker_run_id="run-001",
            action_id="internal.run_tests",
            payload={"suite": "unit"},
        )
    )

    assert outcome.allowed is True
    assert outcome.status == "verified"
    assert calls == ["internal.run_tests"]
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT decision, action_scope, approval_id FROM execution_attempts "
            "WHERE idempotency_key = ?",
            ("internal-run-001",),
        ).fetchone()
    assert row == ("allow", "internal", None)


def test_internal_binding_rejects_request_role_claim_mismatch(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    gateway = ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=ApprovalVerifier({}),
        bindings=ToolBindingRegistry(
            [
                ToolBinding(
                    action_id="internal.run_tests",
                    scope="internal",
                    handler=internal_tool,
                    simulation_only=True,
                    allowed_roles=frozenset({"builder"}),
                )
            ]
        ),
        clock=lambda: NOW,
        kill_switch=KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "research:test-worker", "research", request.worker_run_id
        ),
    )

    outcome = gateway.execute(
        ExecutionRequest(
            idempotency_key="internal-role-mismatch-001",
            actor_role="builder",
            worker_run_id="run-001",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "actor_identity_mismatch"
    assert calls == []
    _assert_denial_record(database_path, "internal-role-mismatch-001", "actor_identity_mismatch")



def test_global_kill_switch_blocks_internal_tool_execution(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test", True, True)

    kill_switch = KillSwitch()
    gateway = _make_internal_gateway(
        database_path, internal_tool, kill_switch=kill_switch
    )
    kill_switch.activate()
    outcome = gateway.execute(
        ExecutionRequest(
            idempotency_key="internal-stop-001",
            actor_role="builder",
            worker_run_id="run-001",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "kill_switch_active"
    assert calls == []


def test_record_payout_state_is_a_known_founder_approval_action():
    decision = evaluate_action(ActionRequest(role="builder", action="record_payout_state"))

    assert decision.allowed is False
    assert decision.founder_approval_required is True
    assert decision.reason == "founder_approval_required"


@pytest.mark.parametrize(
    ("field", "value", "bound_action"),
    [
        ("experiment_id", "CEO-005-001", "publish_listing"),
        ("action_id", "contact_customer", "contact_customer"),
        ("offer_id", "offer-002", "publish_listing"),
        ("channel_id", "other-channel", "publish_listing"),
    ],
)
def test_approval_scope_mismatch_is_denied(field, value, bound_action, tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    simulator = SimulatedExternalTool(calls)

    outcome = _make_gateway(
        database_path, public_key, simulator, action_id=bound_action
    ).execute(_execution_request(approval, **{field: value}))

    assert outcome.allowed is False
    assert outcome.reason == "approval_scope_mismatch"
    assert calls == []


@pytest.mark.parametrize(
    ("approval_field", "request_field", "approval_value"),
    [
        ("approved_offer", "offer_id", None),
        ("approved_offer", "offer_id", ""),
        ("approved_channel", "channel_id", None),
        ("approved_channel", "channel_id", ""),
    ],
)
def test_approval_record_requires_nonempty_offer_and_channel_scope(
    approval_field, request_field, approval_value, tmp_path
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(
        private_key, **{approval_field: approval_value}
    )
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    request_scope = {
        "offer_id": "offer-001",
        "channel_id": "upwork-project-catalog",
    }
    request_scope[request_field] = "valid-scope-value"

    outcome = _make_gateway(
        database_path, public_key, SimulatedExternalTool(calls)
    ).execute(_execution_request(approval, **request_scope))

    assert outcome.allowed is False
    assert outcome.reason == "invalid_approval_scope"
    assert calls == []


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("offer_id", None, "invalid_offer_id"),
        ("offer_id", "", "invalid_offer_id"),
        ("channel_id", None, "invalid_channel_id"),
        ("channel_id", "", "invalid_channel_id"),
    ],
)
def test_external_request_requires_nonempty_offer_and_channel_before_reserving(
    field, value, reason, tmp_path
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool([]))
    trusted_provider = gateway.principal_provider
    provider_calls = []

    def tracked_provider(request):
        provider_calls.append(request.action_id)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    request = _execution_request(
        approval,
        idempotency_key=f"missing-scope-{field}-{value}",
        **{field: value},
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == reason
    assert outcome.attempt_id is None
    assert provider_calls == []
    with sqlite3.connect(database_path) as connection:
        denial = connection.execute(
            "SELECT idempotency_key, decision, reason FROM execution_attempts "
            "WHERE reason = ?",
            (reason,),
        ).fetchone()
        caller_key_attempts = connection.execute(
            "SELECT COUNT(*) FROM execution_attempts WHERE idempotency_key = ?",
            (request.idempotency_key,),
        ).fetchone()[0]
    assert denial is not None
    assert denial[0].startswith("gateway-denial-")
    assert denial[1:] == ("deny", reason)
    assert caller_key_attempts == 0

    correct_scope_value = (
        approval.approved_offer
        if field == "offer_id"
        else approval.approved_channel
    )
    retry = gateway.execute(replace(request, **{field: correct_scope_value}))
    assert retry.allowed is True
    assert retry.status == "verified"


def test_external_request_without_approval_is_denied_and_audited(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    _, public_key = _key_pair()
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        ExecutionRequest(
            idempotency_key="missing-approval-001",
            actor_role="allocator",
            worker_run_id="run-001",
            action_id="publish_listing",
            experiment_id="CEO-004-001",
            offer_id="offer-001",
            channel_id="upwork-project-catalog",
            transaction_value_usd=1.0,
            payload={},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "missing_approval_record"
    assert calls == []
    _assert_denial_record(database_path, "missing-approval-001", "missing_approval_record")


def test_expired_approval_is_denied(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key, expires_at=NOW - timedelta(seconds=1))
    ApprovalStore(database_path).add_approval(approval)
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        _execution_request(approval, idempotency_key="expired-approval-001")
    )

    assert outcome.allowed is False
    assert outcome.reason == "approval_expired_or_not_yet_valid"
    assert calls == []


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("transaction_value_usd", 100.01, "transaction_value_cap_exceeded"),
        ("direct_spend_usd", 0.01, "direct_spend_cap_exceeded"),
        ("founder_attention_minutes", 30.01, "founder_attention_cap_exceeded"),
        ("delivery_labor_hours", 3.01, "delivery_labor_cap_exceeded"),
    ],
)
def test_execution_request_cannot_exceed_signed_caps(field, value, reason, tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        _execution_request(
            approval,
            idempotency_key=f"cap-{field}",
            **{field: value},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == reason
    assert calls == []


@pytest.mark.parametrize(
    ("field", "cap_field", "reason"),
    [
        ("direct_spend_usd", "max_direct_spend_usd", "direct_spend_cap_exceeded"),
        (
            "founder_attention_minutes",
            "max_founder_attention_minutes",
            "founder_attention_cap_exceeded",
        ),
        (
            "delivery_labor_hours",
            "max_delivery_labor_hours",
            "delivery_labor_cap_exceeded",
        ),
    ],
)
def test_cumulative_caps_do_not_round_low_order_amount_digits(
    field, cap_field, reason, tmp_path
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, _ = _key_pair()
    exposure = replace(_exposure_request(), **{cap_field: 1e20})
    approval = _signed_approval(private_key, exposure=exposure)
    request = _execution_request(
        approval,
        idempotency_key=f"exact-cap-{field}",
        **{field: Decimal("100000000000000000000.0000000001")},
    )

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        cap_reason = ExecutionGateway._check_caps(connection, request, approval)

    assert cap_reason == reason


def test_transaction_count_limit_is_enforced_across_attempts(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))

    first = gateway.execute(
        _execution_request(approval, idempotency_key="transaction-001")
    )
    second = gateway.execute(
        _execution_request(approval, idempotency_key="transaction-002")
    )

    assert first.status == "verified"
    assert second.allowed is False
    assert second.reason == "transaction_count_cap_exceeded"
    assert calls == ["publish_listing"]


def test_class_c_risk_is_prohibited_even_with_valid_founder_signature(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    class_c_exposure = replace(_exposure_request(), risk_flags=frozenset({"borrowing"}))
    approval = _signed_approval(private_key, risk_class="C", exposure=class_c_exposure)
    ApprovalStore(database_path).add_approval(approval)
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        _execution_request(approval, idempotency_key="class-c-001")
    )

    assert outcome.allowed is False
    assert outcome.reason == "class_c_prohibited"
    assert calls == []


def test_unregistered_external_action_is_denied_and_audited(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        _execution_request(
            approval,
            idempotency_key="unregistered-001",
            action_id="external.unregistered_tool",
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "unregistered_action"
    assert calls == []
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT decision, action_scope, reason FROM execution_attempts "
            "WHERE idempotency_key = ?",
            ("unregistered-001",),
        ).fetchone()
    assert row == ("deny", "unknown", "unregistered_action")


def test_registry_refuses_live_external_tool_bindings():
    def live_tool(request: ExecutionRequest) -> ToolResult:
        return ToolResult(request.action_id, request.approval_id, "live:ref", True, False)

    with pytest.raises(ValueError, match="live external tool bindings are disabled"):
        ToolBindingRegistry(
            [
                ToolBinding(
                    action_id="publish_listing",
                    scope="external",
                    handler=live_tool,
                    simulation_only=False,
                )
            ]
        )


def test_simulation_flag_alone_cannot_bind_an_external_callable():
    def untrusted_handler(request: ExecutionRequest) -> ToolResult:
        return ToolResult(request.action_id, request.approval_id, "simulated:fake", True, True)

    with pytest.raises(ValueError, match="external tool callables are disabled"):
        ToolBindingRegistry(
            [
                ToolBinding(
                    action_id="publish_listing",
                    scope="external",
                    handler=untrusted_handler,
                    simulation_only=True,
                )
            ]
        )


def test_idempotency_key_conflict_is_denied_and_audited(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))

    first = gateway.execute(
        _execution_request(approval, idempotency_key="same-key-001", payload={"v": "first"})
    )
    conflict = gateway.execute(
        _execution_request(approval, idempotency_key="same-key-001", payload={"v": "changed"})
    )

    assert first.status == "verified"
    assert conflict.allowed is False
    assert conflict.reason == "idempotency_key_conflict"
    assert calls == ["publish_listing"]
    with sqlite3.connect(database_path) as connection:
        event = connection.execute(
            "SELECT event_type, reason FROM execution_events WHERE idempotency_key = ? "
            "ORDER BY rowid DESC LIMIT 1",
            ("same-key-001",),
        ).fetchone()
    assert event == ("idempotency_key_conflict", "idempotency_key_conflict")


def test_idempotent_replay_returns_prior_result_without_reexecuting(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))
    request = _execution_request(approval, idempotency_key="replay-key-001")

    first = gateway.execute(request)
    replay = gateway.execute(request)

    assert first.status == "verified"
    assert replay.status == "verified"
    assert replay.reason == "idempotent_replay"
    assert replay.attempt_id == first.attempt_id
    assert calls == ["publish_listing"]
    with sqlite3.connect(database_path) as connection:
        event = connection.execute(
            "SELECT event_type FROM execution_events WHERE idempotency_key = ? "
            "ORDER BY rowid DESC LIMIT 1",
            ("replay-key-001",),
        ).fetchone()
    assert event == ("idempotent_replay",)


def test_record_payout_state_uses_approval_gated_simulated_binding(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key, approved_action="record_payout_state")
    ApprovalStore(database_path).add_approval(approval)
    calls = []

    outcome = _make_gateway(
        database_path,
        public_key,
        SimulatedExternalTool(calls),
        action_id="record_payout_state",
    ).execute(_execution_request(approval, idempotency_key="payout-state-001"))

    assert outcome.status == "verified"
    assert calls == ["record_payout_state"]


def test_direct_database_tampering_cannot_change_signed_approval_scope(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    with sqlite3.connect(database_path) as connection:
        payload_json = connection.execute(
            "SELECT payload_json FROM approval_records WHERE approval_id = ?",
            (approval.approval_id,),
        ).fetchone()[0]
        payload = json.loads(payload_json)
        payload["approved_offer"] = "offer-tampered"
        connection.execute("DROP TRIGGER approval_records_no_update")
        connection.execute(
            "UPDATE approval_records SET payload_json = ? WHERE approval_id = ?",
            (json.dumps(payload, sort_keys=True, separators=(",", ":")), approval.approval_id),
        )
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        _execution_request(approval, idempotency_key="tampered-row-001")
    )

    assert outcome.allowed is False
    assert outcome.reason == "invalid_approval_signature"
    assert calls == []


def test_fractional_second_tampering_cannot_extend_signed_approval_expiry(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)

    with sqlite3.connect(database_path) as connection:
        payload_json = connection.execute(
            "SELECT payload_json FROM approval_records WHERE approval_id = ?",
            (approval.approval_id,),
        ).fetchone()[0]
        payload = json.loads(payload_json)
        payload["expires_at"] = payload["expires_at"].replace("Z", ".999999Z")
        connection.execute("DROP TRIGGER approval_records_no_update")
        connection.execute(
            "UPDATE approval_records SET payload_json = ? WHERE approval_id = ?",
            (
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                approval.approval_id,
            ),
        )
    calls = []

    outcome = _make_gateway(
        database_path, public_key, SimulatedExternalTool(calls)
    ).execute(_execution_request(approval, idempotency_key="fractional-expiry-001"))

    assert outcome.allowed is False
    assert outcome.reason == "invalid_approval_record"
    assert calls == []


def test_unsafe_tool_result_reference_is_not_logged_or_verified(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    unsafe_reference = "internal:token=fixture-only"

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        return ToolResult(request.action_id, None, unsafe_reference, True, True)

    outcome = _make_internal_gateway(database_path, internal_tool).execute(
        ExecutionRequest(
            idempotency_key="unsafe-result-001",
            actor_role="builder",
            worker_run_id="run-001",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.allowed is True
    assert outcome.status == "verification_failed"
    with sqlite3.connect(database_path) as connection:
        status, result_json = connection.execute(
            "SELECT status, result_json FROM execution_results WHERE attempt_id = ?",
            (outcome.attempt_id,),
        ).fetchone()
    assert status == "verification_failed"
    assert unsafe_reference not in result_json


@pytest.mark.parametrize(
    "tool_reference",
    [
        "sk_live_" + "a" * 32,
        "a" * 64,
    ],
    ids=["live-token-shape", "long-hex"],
)
def test_tool_result_reference_is_replaced_before_persistence_and_return(
    tmp_path, tool_reference
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        return ToolResult(request.action_id, None, tool_reference, True, True)

    gateway = _make_internal_gateway(database_path, internal_tool)
    request = ExecutionRequest(
        idempotency_key="opaque-result-reference-001",
        actor_role="builder",
        worker_run_id="run-opaque-result",
        action_id="internal.run_tests",
        payload={},
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is True
    assert outcome.status == "verified"
    assert outcome.attempt_id is not None
    assert outcome.result is not None
    opaque_reference = f"gateway-result:{outcome.attempt_id}"
    assert outcome.result.external_ref == opaque_reference
    assert tool_reference not in repr(outcome)
    with sqlite3.connect(database_path) as connection:
        result_json = connection.execute(
            "SELECT result_json FROM execution_results WHERE attempt_id = ?",
            (outcome.attempt_id,),
        ).fetchone()[0]
    assert tool_reference not in result_json
    assert json.loads(result_json)["external_ref"] == opaque_reference

    replay = gateway.execute(request)
    assert replay.allowed is True
    assert replay.status == "verified"
    assert replay.result is not None
    assert replay.result.external_ref == opaque_reference
    assert tool_reference not in repr(replay)


def test_internal_result_metadata_must_not_persist_non_boolean_values(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    secret_metadata = "sk_live_" + "b" * 32

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        return ToolResult(
            request.action_id,
            None,
            "internal:test-run",
            True,
            cast(bool, secret_metadata),
        )

    outcome = _make_internal_gateway(database_path, internal_tool).execute(
        ExecutionRequest(
            idempotency_key="unsafe-result-metadata-001",
            actor_role="builder",
            worker_run_id="run-result-metadata",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.status == "verification_failed"
    assert outcome.attempt_id is not None
    assert secret_metadata not in repr(outcome)
    with sqlite3.connect(database_path) as connection:
        result_json = connection.execute(
            "SELECT result_json FROM execution_results WHERE attempt_id = ?",
            (outcome.attempt_id,),
        ).fetchone()[0]
    assert secret_metadata not in result_json
    assert json.loads(result_json)["error_code"] == "tool_result_verification_failed"


def test_malformed_signed_record_fails_closed_and_is_audited(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key, risk_class=[])
    ApprovalStore(database_path).add_approval(approval)
    calls = []

    outcome = _make_gateway(database_path, public_key, SimulatedExternalTool(calls)).execute(
        _execution_request(approval, idempotency_key="malformed-record-001")
    )

    assert outcome.allowed is False
    assert outcome.reason == "approval_validation_error"
    assert calls == []
    _assert_denial_record(database_path, "malformed-record-001", "approval_validation_error")


def test_tampered_persisted_result_is_not_replayed_as_verified(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))
    request = _execution_request(approval, idempotency_key="tampered-result-001")
    first = gateway.execute(request)
    assert first.status == "verified"

    with sqlite3.connect(database_path) as connection:
        result_json = connection.execute(
            "SELECT result_json FROM execution_results WHERE attempt_id = ?",
            (first.attempt_id,),
        ).fetchone()[0]
        result_payload = json.loads(result_json)
        result_payload["action_id"] = "contact_customer"
        connection.execute("DROP TRIGGER execution_results_no_update")
        connection.execute(
            "UPDATE execution_results SET result_json = ? WHERE attempt_id = ?",
            (json.dumps(result_payload, sort_keys=True, separators=(",", ":")), first.attempt_id),
        )

    replay = gateway.execute(request)

    assert replay.allowed is True
    assert replay.status == "verification_failed"
    assert replay.reason == "stored_result_invalid"
    assert replay.result is None
    assert calls == ["publish_listing"]
    with sqlite3.connect(database_path) as connection:
        event = connection.execute(
            "SELECT event_type, reason FROM execution_events WHERE idempotency_key = ? "
            "ORDER BY rowid DESC LIMIT 1",
            ("tampered-result-001",),
        ).fetchone()
    assert event == ("idempotent_replay", "stored_result_invalid")


def test_approval_and_policy_checks_precede_exact_binding_and_execution(tmp_path, monkeypatch):
    from runtime import approval_gateway as gateway_module

    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    events = []

    class RecordingVerifier(ApprovalVerifier):
        def verify(self, record):
            events.append("approval")
            return super().verify(record)

    original_evaluate = gateway_module.evaluate_action

    def record_policy(request):
        events.append("policy")
        return original_evaluate(request)

    original_simulator_call = SimulatedExternalTool.__call__

    def record_execution(self, request):
        events.append("execute")
        return original_simulator_call(self, request)

    monkeypatch.setattr(gateway_module, "evaluate_action", record_policy)
    monkeypatch.setattr(SimulatedExternalTool, "__call__", record_execution)
    simulator = SimulatedExternalTool()
    binding = ToolBinding(
        action_id="publish_listing",
        scope="external",
        handler=simulator,
        simulation_only=True,
        allowed_roles=frozenset({"allocator"}),
    )

    class RecordingBindings:
        def get(self, action_id: str) -> ToolBinding | None:
            events.append("binding")
            return binding if action_id == binding.action_id else None

    gateway = ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=RecordingVerifier({"founder-test-key": public_key}),
        bindings=RecordingBindings(),
        clock=lambda: NOW,
        kill_switch=KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "allocator:test-worker", "allocator", request.worker_run_id
        ),
    )
    outcome = gateway.execute(_execution_request(approval))

    assert outcome.status == "verified"
    assert events == ["approval", "policy", "binding", "approval", "binding", "execute"]



def test_approval_expiry_is_rechecked_at_execution_boundary(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    clock_values = iter([NOW, NOW + timedelta(days=8)])
    gateway = _make_gateway(
        database_path,
        public_key,
        SimulatedExternalTool(calls),
        clock=lambda: next(clock_values),
    )

    outcome = gateway.execute(_execution_request(approval, idempotency_key="expiry-race-001"))

    assert outcome.allowed is False
    assert outcome.reason == "approval_expired_or_not_yet_valid"
    assert calls == []
    with sqlite3.connect(database_path) as connection:
        event = connection.execute(
            "SELECT event_type, reason FROM execution_events WHERE idempotency_key = ? "
            "AND event_type = 'execution_blocked'",
            ("expiry-race-001",),
        ).fetchone()
    assert event == ("execution_blocked", "approval_expired_or_not_yet_valid")


def test_kill_switch_activation_after_policy_check_blocks_execution(tmp_path, monkeypatch):
    from contextlib import contextmanager

    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    kill_switch = KillSwitch()
    gateway = _make_gateway(
        database_path, public_key, SimulatedExternalTool(calls), kill_switch=kill_switch
    )
    original_transaction = gateway.store.transaction
    activated = False

    @contextmanager
    def activate_after_authorization(*, immediate=False):
        nonlocal activated
        with original_transaction(immediate=immediate) as connection:
            yield connection
        if not activated:
            activated = True
            kill_switch.activate()

    monkeypatch.setattr(gateway.store, "transaction", activate_after_authorization)

    outcome = gateway.execute(_execution_request(approval, idempotency_key="kill-switch-race-001"))

    assert outcome.allowed is False
    assert outcome.reason == "kill_switch_active"
    assert calls == []


def test_result_persistence_failure_is_audited_and_not_reexecuted(tmp_path, monkeypatch):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))
    request = _execution_request(approval, idempotency_key="result-write-failure-001")

    def fail_persistence(attempt_id, status, result):
        raise sqlite3.OperationalError("simulated result write failure")

    monkeypatch.setattr(gateway, "_save_result", fail_persistence)
    first = gateway.execute(request)
    replay = gateway.execute(request)

    assert first.allowed is True
    assert first.status == "result_persistence_failed"
    assert replay.allowed is True
    assert replay.status == "pending"
    assert calls == ["publish_listing"]
    with sqlite3.connect(database_path) as connection:
        events = connection.execute(
            "SELECT event_type, reason FROM execution_events WHERE idempotency_key = ? "
            "ORDER BY rowid",
            ("result-write-failure-001",),
        ).fetchall()
        result_count = connection.execute(
            "SELECT COUNT(*) FROM execution_results WHERE attempt_id = ?",
            (first.attempt_id,),
        ).fetchone()[0]
    assert ("execution_reserved", "handler_invocation_reserved") in events
    assert ("result_persistence_failed", "result_persistence_failed") in events
    assert result_count == 0



def test_internal_binding_rejects_authenticated_role_outside_allowlist(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    gateway = ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=ApprovalVerifier({}),
        bindings=ToolBindingRegistry(
            [
                ToolBinding(
                    action_id="internal.run_tests",
                    scope="internal",
                    handler=internal_tool,
                    simulation_only=True,
                    allowed_roles=frozenset({"builder"}),
                )
            ]
        ),
        clock=lambda: NOW,
        kill_switch=KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "research:test-worker", "research", request.worker_run_id
        ),
    )
    outcome = gateway.execute(
        ExecutionRequest(
            idempotency_key="internal-role-allowlist-001",
            actor_role="research",
            worker_run_id="run-001",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "role_not_permitted"
    assert calls == []
    _assert_denial_record(database_path, "internal-role-allowlist-001", "role_not_permitted")


def test_external_replay_rechecks_authenticated_role_before_returning_result(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    principals = [TrustedPrincipal("allocator:one", "allocator", "run-001")]
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))
    gateway.principal_provider = lambda request: principals[0]
    request = _execution_request(approval, idempotency_key="replay-role-check-001")

    first = gateway.execute(request)
    principals[0] = TrustedPrincipal("research:one", "research", "run-001")
    replay = gateway.execute(request)

    assert first.status == "verified"
    assert replay.allowed is False
    assert replay.reason == "actor_identity_mismatch"
    assert replay.result is None
    assert calls == ["publish_listing"]


def test_replay_with_different_worker_run_is_denied(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))
    gateway.principal_provider = lambda request: TrustedPrincipal(
        "allocator:one", "allocator", "run-001"
    )
    request = _execution_request(approval, idempotency_key="replay-run-check-001")

    first = gateway.execute(request)
    replay = gateway.execute(replace(request, worker_run_id="different-run"))

    assert first.status == "verified"
    assert replay.allowed is False
    assert replay.reason == "worker_run_identity_mismatch"
    assert replay.result is None
    assert calls == ["publish_listing"]


def test_replay_with_different_trusted_principal_is_denied(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    principals = [TrustedPrincipal("allocator:one", "allocator", "run-001")]
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool(calls))
    gateway.principal_provider = lambda request: principals[0]
    request = _execution_request(approval, idempotency_key="replay-principal-check-001")

    first = gateway.execute(request)
    principals[0] = TrustedPrincipal("allocator:two", "allocator", "run-001")
    replay = gateway.execute(request)

    assert first.status == "verified"
    assert replay.allowed is False
    assert replay.reason == "idempotency_key_conflict"
    assert replay.result is None
    assert calls == ["publish_listing"]


def test_active_kill_switch_denies_external_replay(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []
    kill_switch = KillSwitch()
    gateway = _make_gateway(
        database_path, public_key, SimulatedExternalTool(calls), kill_switch=kill_switch
    )
    request = _execution_request(approval, idempotency_key="replay-kill-switch-001")

    first = gateway.execute(request)
    kill_switch.activate()
    replay = gateway.execute(request)

    assert first.status == "verified"
    assert replay.allowed is False
    assert replay.reason == "kill_switch_active"
    assert replay.result is None
    assert calls == ["publish_listing"]


def test_internal_replay_rechecks_authenticated_role(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    gateway = _make_internal_gateway(database_path, internal_tool)
    request = ExecutionRequest(
        idempotency_key="internal-replay-role-001",
        actor_role="builder",
        worker_run_id="run-001",
        action_id="internal.run_tests",
        payload={},
    )

    principals = [TrustedPrincipal("builder:one", "builder", "run-001")]
    gateway.principal_provider = lambda request: principals[0]
    first = gateway.execute(request)
    principals[0] = TrustedPrincipal("research:one", "research", "run-001")
    replay = gateway.execute(request)

    assert first.status == "verified"
    assert replay.allowed is False
    assert replay.reason == "actor_identity_mismatch"
    assert replay.result is None
    assert calls == ["internal.run_tests"]


def test_kill_switch_closes_admission_while_internal_action_is_in_flight(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    kill_switch = KillSwitch()
    handler_started = Event()
    release_handler = Event()
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.idempotency_key)
        if request.idempotency_key == "kill-flight-first":
            handler_started.set()
            assert release_handler.wait(timeout=3)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    gateway = _make_internal_gateway(database_path, internal_tool, kill_switch=kill_switch)
    first_request = ExecutionRequest(
        idempotency_key="kill-flight-first",
        actor_role="builder",
        worker_run_id="run-001",
        action_id="internal.run_tests",
        payload={},
    )
    first_outcomes = []
    first_thread = Thread(target=lambda: first_outcomes.append(gateway.execute(first_request)))
    first_thread.start()
    assert handler_started.wait(timeout=2)

    activation_returned = Event()
    activation_thread = Thread(
        target=lambda: (kill_switch.activate(), activation_returned.set())
    )
    activation_thread.start()
    second_request = replace(first_request, idempotency_key="kill-flight-second")

    try:
        assert activation_returned.wait(timeout=2)
        second = gateway.execute(second_request)
    finally:
        release_handler.set()
        first_thread.join(timeout=3)
        activation_thread.join(timeout=3)

    assert not first_thread.is_alive()
    assert not activation_thread.is_alive()
    assert first_outcomes[0].status == "verified"
    assert second.allowed is False
    assert second.reason == "kill_switch_active"
    assert calls == ["kill-flight-first"]


def test_kill_switch_state_is_shared_across_gateway_instances(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    first_gateway = _make_internal_gateway(database_path, internal_tool, kill_switch=KillSwitch())
    first_gateway.kill_switch.activate()
    second_gateway = _make_internal_gateway(database_path, internal_tool, kill_switch=KillSwitch())
    outcome = second_gateway.execute(
        ExecutionRequest(
            idempotency_key="shared-kill-switch-001",
            actor_role="builder",
            worker_run_id="run-002",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "kill_switch_active"
    assert calls == []
    with sqlite3.connect(database_path) as connection:
        active = connection.execute(
            "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
            ("global",),
        ).fetchone()[0]
    assert active == 1


def test_new_gateway_control_defaults_to_fail_closed(tmp_path):
    database_path = tmp_path / "gateway.db"
    schema_path = Path(__file__).resolve().parents[1] / "runtime" / "schema.sql"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        active = connection.execute(
            "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
            ("global",),
        ).fetchone()[0]

    assert active == 1



def test_gateway_rejects_live_external_binding_from_custom_provider(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    calls = []

    def live_external_handler(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(
            request.action_id, request.approval_id, "live:external-side-effect", True, True
        )

    class UntrustedBindingProvider:
        def get(self, action_id):
            if action_id != "publish_listing":
                return None
            return ToolBinding(
                action_id="publish_listing",
                scope="external",
                handler=live_external_handler,
                simulation_only=True,
                allowed_roles=frozenset({"allocator"}),
            )

    gateway = ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=ApprovalVerifier({"founder-test-key": public_key}),
        bindings=UntrustedBindingProvider(),
        clock=lambda: NOW,
        kill_switch=KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "allocator:test-worker", "allocator", request.worker_run_id
        ),
    )
    request = _execution_request(approval, idempotency_key="custom-live-binding-001")

    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "live_external_tool_disabled"
    assert calls == []
    _assert_denial_record(
        database_path, "custom-live-binding-001", "live_external_tool_disabled"
    )



def test_restart_with_inactive_constructor_cannot_clear_persisted_kill_switch(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    first_gateway = _make_internal_gateway(database_path, internal_tool)
    first_gateway.kill_switch.activate()
    restarted_gateway = _make_internal_gateway(
        database_path, internal_tool, kill_switch=KillSwitch(active=False)
    )
    outcome = restarted_gateway.execute(
        ExecutionRequest(
            idempotency_key="restart-kill-switch-001",
            actor_role="builder",
            worker_run_id="run-restarted",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "kill_switch_active"
    assert calls == []
    with sqlite3.connect(database_path) as connection:
        active = connection.execute(
            "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
            ("global",),
        ).fetchone()[0]
    assert active == 1



def test_gateway_revalidates_custom_binding_at_final_admission(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    simulator_calls = []
    live_calls = []
    simulator = SimulatedExternalTool(simulator_calls)

    def live_external_handler(request: ExecutionRequest) -> ToolResult:
        live_calls.append(request.action_id)
        return ToolResult(
            request.action_id, request.approval_id, "live:external-side-effect", True, True
        )

    class SwitchingBindingProvider:
        def __init__(self):
            self.lookup_count = 0

        def get(self, action_id):
            self.lookup_count += 1
            handler = simulator if self.lookup_count == 1 else live_external_handler
            return ToolBinding(
                action_id=action_id,
                scope="external",
                handler=handler,
                simulation_only=True,
                allowed_roles=frozenset({"allocator"}),
            )

    gateway = ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=ApprovalVerifier({"founder-test-key": public_key}),
        bindings=SwitchingBindingProvider(),
        clock=lambda: NOW,
        kill_switch=KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "allocator:test-worker", "allocator", request.worker_run_id
        ),
    )

    outcome = gateway.execute(
        _execution_request(approval, idempotency_key="binding-switch-001")
    )

    assert outcome.allowed is False
    assert outcome.reason == "live_external_tool_disabled"
    assert simulator_calls == []
    assert live_calls == []
    with sqlite3.connect(database_path) as connection:
        event = connection.execute(
            "SELECT event_type, reason FROM execution_events "
            "WHERE idempotency_key = ? ORDER BY rowid DESC LIMIT 1",
            ("binding-switch-001",),
        ).fetchone()
    assert event == ("execution_blocked", "live_external_tool_disabled")



def test_gateway_rejects_simulator_with_overridden_call_log_from_custom_provider(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    side_effects = []

    class SideEffectList(list):
        def append(self, value):
            side_effects.append(value)
            super().append(value)

    simulator = SimulatedExternalTool()
    object.__setattr__(simulator, "_observer", SideEffectList())

    class CustomBindingProvider:
        def get(self, action_id):
            return ToolBinding(
                action_id=action_id,
                scope="external",
                handler=simulator,
                simulation_only=True,
                allowed_roles=frozenset({"allocator"}),
            )

    gateway = ExecutionGateway(
        store=ApprovalStore(database_path),
        verifier=ApprovalVerifier({"founder-test-key": public_key}),
        bindings=CustomBindingProvider(),
        clock=lambda: NOW,
        kill_switch=KillSwitch(),
        principal_provider=lambda request: TrustedPrincipal(
            "allocator:test-worker", "allocator", request.worker_run_id
        ),
    )
    outcome = gateway.execute(
        _execution_request(approval, idempotency_key="simulator-sink-001")
    )

    assert outcome.allowed is False
    assert outcome.reason == "live_external_tool_disabled"
    assert side_effects == []
    _assert_denial_record(
        database_path, "simulator-sink-001", "live_external_tool_disabled"
    )



def test_simulator_rejects_overridden_call_log_sink():
    side_effects = []

    class SideEffectList(list):
        def append(self, value):
            side_effects.append(value)
            super().append(value)

    with pytest.raises(TypeError, match="built-in list"):
        SimulatedExternalTool(SideEffectList())
    assert side_effects == []


def test_internal_request_cannot_claim_experiment_cap_usage(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:test-run", True, True)

    request = ExecutionRequest(
        idempotency_key="internal-cap-claim-001",
        actor_role="builder",
        worker_run_id="run-001",
        action_id="internal.run_tests",
        experiment_id="CEO-004-001",
        offer_id="b2b-competitor-facts-brief",
        channel_id="upwork-project-catalog",
        founder_attention_minutes=30.0,
        delivery_labor_hours=3.0,
        payload={"suite": "unit"},
    )
    outcome = _make_internal_gateway(database_path, internal_tool).execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "internal_action_cannot_claim_experiment_usage"
    assert calls == []
    _assert_denial_record(
        database_path,
        "internal-cap-claim-001",
        "internal_action_cannot_claim_experiment_usage",
    )


def test_internal_attempts_do_not_consume_external_experiment_caps(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)

    # Simulate a legacy internal record carrying untrusted experiment usage claims.
    legacy_request = ExecutionRequest(
        idempotency_key="legacy-internal-cap-001",
        actor_role="builder",
        worker_run_id="run-legacy",
        action_id="internal.run_tests",
        approval_id=approval.approval_id,
        experiment_id=approval.experiment_id,
        offer_id=approval.approved_offer,
        channel_id=approval.approved_channel,
        transaction_value_usd=100.0,
        founder_attention_minutes=30.0,
        delivery_labor_hours=3.0,
        payload={},
    )
    with sqlite3.connect(database_path) as connection:
        ExecutionGateway._insert_attempt(
            connection,
            "legacy-internal-attempt",
            "legacy-internal-cap-001",
            legacy_request,
            "internal",
            "allow",
            "result_verified",
            "legacy-request-digest",
            NOW.isoformat(),
            principal_id="builder:legacy-worker",
        )

    calls = []
    outcome = _make_gateway(
        database_path, public_key, SimulatedExternalTool(calls)
    ).execute(_execution_request(approval, idempotency_key="after-legacy-internal-001"))

    assert outcome.allowed is True
    assert outcome.status == "verified"
    assert calls == ["publish_listing"]


def test_unauthenticated_replay_does_not_mutate_or_disclose_existing_attempt(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    gateway = _make_gateway(
        database_path, public_key, SimulatedExternalTool([])
    )
    request = _execution_request(approval, idempotency_key="unauthenticated-replay-001")
    first = gateway.execute(request)
    assert first.status == "verified"
    assert first.attempt_id is not None

    with sqlite3.connect(database_path) as connection:
        before = connection.execute(
            "SELECT COUNT(*) FROM execution_events WHERE attempt_id = ?",
            (first.attempt_id,),
        ).fetchone()[0]

    principal_calls = []

    def unauthenticated_provider(_request):
        principal_calls.append("called")
        raise RuntimeError("no authenticated principal")

    gateway.principal_provider = unauthenticated_provider
    malformed_payload_outcome = gateway.execute(
        replace(request, payload={"invalid": object()})
    )
    assert malformed_payload_outcome.allowed is False
    assert malformed_payload_outcome.reason == "invalid_request_payload"
    assert malformed_payload_outcome.attempt_id is None

    unregistered_action_outcome = gateway.execute(
        replace(request, action_id="unregistered_action")
    )
    assert unregistered_action_outcome.allowed is False
    assert unregistered_action_outcome.reason == "trusted_identity_unavailable"
    assert unregistered_action_outcome.attempt_id is None

    with sqlite3.connect(database_path) as connection:
        after = connection.execute(
            "SELECT COUNT(*) FROM execution_events WHERE attempt_id = ?",
            (first.attempt_id,),
        ).fetchone()[0]
        unauthenticated_denials = connection.execute(
            """SELECT COUNT(*) FROM execution_attempts
               WHERE decision = 'deny'
                 AND reason = 'trusted_identity_unavailable'
                 AND principal_id = 'unknown'"""
        ).fetchone()[0]
        malformed_payload_denials = connection.execute(
            """SELECT COUNT(*) FROM execution_attempts
               WHERE decision = 'deny'
                 AND reason = 'invalid_request_payload'
                 AND principal_id = 'unknown'"""
        ).fetchone()[0]
        collision_relations = connection.execute(
            """SELECT COUNT(*) FROM execution_attempt_relations
               WHERE relation_type = 'idempotency_collision'
                 AND target_attempt_digest = ?
                 AND idempotency_key_digest = ?""",
            (
                hashlib.sha256(first.attempt_id.encode("utf-8")).hexdigest(),
                hashlib.sha256(request.idempotency_key.encode("utf-8")).hexdigest(),
            ),
        ).fetchone()[0]
    assert principal_calls == ["called"]
    assert after == before
    assert unauthenticated_denials == 1
    assert malformed_payload_denials == 1
    assert collision_relations == 2


def test_unauthenticated_request_does_not_reserve_idempotency_key(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool([]))
    trusted_provider = gateway.principal_provider
    request = _execution_request(approval, idempotency_key="fresh-unauth-key-001")

    def unauthenticated_provider(_request):
        raise RuntimeError("no authenticated principal")

    gateway.principal_provider = unauthenticated_provider
    denied = gateway.execute(request)
    assert denied.allowed is False
    assert denied.reason == "trusted_identity_unavailable"
    assert denied.attempt_id is None

    gateway.principal_provider = trusted_provider
    allowed = gateway.execute(request)
    assert allowed.allowed is True
    assert allowed.status == "verified"


def test_authenticated_principal_collision_is_audited_detached(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool([]))
    request = _execution_request(approval, idempotency_key="authenticated-collision-001")
    first = gateway.execute(request)
    assert first.status == "verified"
    assert first.attempt_id is not None

    with sqlite3.connect(database_path) as connection:
        original_events = connection.execute(
            "SELECT COUNT(*) FROM execution_events WHERE attempt_id = ?",
            (first.attempt_id,),
        ).fetchone()[0]

    gateway.principal_provider = lambda _request: TrustedPrincipal(
        "allocator:other-worker", "allocator", "run-001"
    )
    collision = gateway.execute(request)
    assert collision.allowed is False
    assert collision.reason == "idempotency_key_conflict"
    assert collision.attempt_id is None

    with sqlite3.connect(database_path) as connection:
        events_after = connection.execute(
            "SELECT COUNT(*) FROM execution_events WHERE attempt_id = ?",
            (first.attempt_id,),
        ).fetchone()[0]
        audit = connection.execute(
            """SELECT a.idempotency_key, a.decision, a.principal_id, a.reason,
                      r.target_attempt_digest, r.idempotency_key_digest
               FROM execution_attempts AS a
               JOIN execution_attempt_relations AS r
                 ON r.denial_attempt_id = a.attempt_id
               WHERE r.relation_type = 'idempotency_collision'
                 AND a.reason = 'idempotency_key_conflict'"""
        ).fetchone()

    assert events_after == original_events
    assert audit is not None
    assert audit[0].startswith("gateway-denial-")
    assert audit[0] != request.idempotency_key
    assert audit[1:4] == (
        "deny",
        "allocator:other-worker",
        "idempotency_key_conflict",
    )
    assert audit[4] == hashlib.sha256(first.attempt_id.encode("utf-8")).hexdigest()
    assert audit[5] == hashlib.sha256(request.idempotency_key.encode("utf-8")).hexdigest()


def test_internal_handler_receives_frozen_payload_snapshot(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    caller_payload = {"nested": {"items": ["before-admission"]}}
    handler_requests = []

    def internal_handler(request: ExecutionRequest) -> ToolResult:
        caller_payload["nested"]["items"][0] = "changed-after-admission"
        handler_requests.append(request)
        return ToolResult(
            request.action_id, None, "internal:payload-snapshot", True, True
        )

    gateway = _make_internal_gateway(database_path, internal_handler)
    request = ExecutionRequest(
        idempotency_key="payload-snapshot-001",
        actor_role="builder",
        worker_run_id="run-payload-snapshot",
        action_id="internal.run_tests",
        payload=caller_payload,
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is True
    assert outcome.status == "verified"
    assert caller_payload["nested"]["items"][0] == "changed-after-admission"
    assert len(handler_requests) == 1
    handler_request = handler_requests[0]
    assert handler_request.payload is not None
    mapping_proxy_type = type(MappingProxyType({}))
    assert type(handler_request.payload) is mapping_proxy_type
    nested_payload = handler_request.payload["nested"]
    assert type(nested_payload) is mapping_proxy_type
    items = nested_payload["items"]
    assert type(items) is tuple
    assert items == ("before-admission",)

    with sqlite3.connect(database_path) as connection:
        stored_digest = connection.execute(
            "SELECT request_digest FROM execution_attempts WHERE idempotency_key = ?",
            (request.idempotency_key,),
        ).fetchone()[0]
    principal = TrustedPrincipal(
        "builder:test-worker", "builder", "run-payload-snapshot"
    )
    assert stored_digest == _request_digest(handler_request, principal)


def test_payload_none_request_is_snapshotted_before_handler(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    source_request = []
    handler_requests = []

    def internal_handler(request: ExecutionRequest) -> ToolResult:
        object.__setattr__(source_request[0], "action_id", "internal.mutated")
        handler_requests.append(request)
        return ToolResult(
            request.action_id, None, "internal:none-payload", True, True
        )

    gateway = _make_internal_gateway(database_path, internal_handler)
    request = ExecutionRequest(
        idempotency_key="payload-none-snapshot-001",
        actor_role="builder",
        worker_run_id="run-payload-none",
        action_id="internal.run_tests",
    )
    source_request.append(request)

    outcome = gateway.execute(request)

    assert outcome.allowed is True
    assert outcome.status == "verified"
    assert source_request[0].action_id == "internal.mutated"
    assert len(handler_requests) == 1
    handler_request = handler_requests[0]
    assert handler_request is not source_request[0]
    assert handler_request.action_id == "internal.run_tests"
    with sqlite3.connect(database_path) as connection:
        stored_digest = connection.execute(
            "SELECT request_digest FROM execution_attempts WHERE idempotency_key = ?",
            (request.idempotency_key,),
        ).fetchone()[0]
    principal = TrustedPrincipal("builder:test-worker", "builder", "run-payload-none")
    assert stored_digest == _request_digest(handler_request, principal)


@pytest.mark.parametrize(
    "payload",
    [
        {"body": "x" * 1_000_000},
        {"control": "\x00" * 50_000},
        {"items": list(range(5_000))},
        _deeply_nested_payload(80),
    ],
    ids=["byte-limit", "canonical-byte-limit", "item-limit", "depth-limit"],
)
def test_unbounded_payload_is_rejected_before_authentication(tmp_path, payload):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    handler_calls = []

    def internal_handler(request):
        handler_calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:bounded", True, True)

    gateway = _make_internal_gateway(database_path, internal_handler)
    trusted_provider = gateway.principal_provider
    principal_calls = []

    def tracked_provider(request):
        principal_calls.append(request.action_id)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    request = ExecutionRequest(
        idempotency_key="oversized-payload-key-001",
        actor_role="builder",
        worker_run_id="run-oversized-payload",
        action_id="internal.run_tests",
        payload=payload,
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "invalid_request_payload"
    assert outcome.attempt_id is None
    assert principal_calls == []
    assert handler_calls == []
    with sqlite3.connect(database_path) as connection:
        audit = connection.execute(
            """SELECT idempotency_key, decision, reason FROM execution_attempts
               WHERE reason = 'invalid_request_payload'"""
        ).fetchone()
        caller_key_attempts = connection.execute(
            "SELECT COUNT(*) FROM execution_attempts WHERE idempotency_key = ?",
            (request.idempotency_key,),
        ).fetchone()[0]
    assert audit is not None
    assert audit[0].startswith("gateway-denial-")
    assert audit[1:] == ("deny", "invalid_request_payload")
    assert caller_key_attempts == 0


@pytest.mark.parametrize(
    "amount",
    [Decimal("1e100000000"), Decimal("1e-100000000")],
    ids=["huge-positive-exponent", "huge-negative-exponent"],
)
def test_extreme_decimal_exponents_are_rejected_before_formatting(
    tmp_path, monkeypatch, amount
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    gateway = _make_internal_gateway(
        database_path,
        lambda request: ToolResult(request.action_id, None, "internal:never", True, True),
    )
    trusted_provider = gateway.principal_provider
    principal_calls = []

    def tracked_provider(request):
        principal_calls.append(request.action_id)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    dangerous_formatting = []
    original_amount_text = approval_gateway_module._amount_text

    def bounded_amount_text(value):
        if type(value) is Decimal:
            exponent = value.as_tuple().exponent
            if type(exponent) is int and (
                abs(exponent) > 128 or abs(value.adjusted()) > 128
            ):
                dangerous_formatting.append(exponent)
                return "intercepted-oversized-decimal"
        return original_amount_text(value)

    monkeypatch.setattr(
        approval_gateway_module, "_amount_text", bounded_amount_text
    )
    request = ExecutionRequest(
        idempotency_key="extreme-decimal-key-001",
        actor_role="builder",
        worker_run_id="run-extreme-decimal",
        action_id="internal.run_tests",
        transaction_value_usd=amount,
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "invalid_amount"
    assert outcome.attempt_id is None
    assert principal_calls == []
    assert dangerous_formatting == []


def test_invalid_amount_is_audited_without_reserving_caller_key(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool([]))
    trusted_provider = gateway.principal_provider
    provider_calls = []

    def tracked_provider(request):
        provider_calls.append(request)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    request = _execution_request(
        approval,
        idempotency_key="invalid-amount-key-001",
        direct_spend_usd=-1,
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "invalid_amount"
    assert outcome.attempt_id is None
    assert provider_calls == []
    with sqlite3.connect(database_path) as connection:
        audit = connection.execute(
            """SELECT idempotency_key, decision, reason
               FROM execution_attempts WHERE reason = 'invalid_amount'"""
        ).fetchone()
        caller_key_attempts = connection.execute(
            "SELECT COUNT(*) FROM execution_attempts WHERE idempotency_key = ?",
            (request.idempotency_key,),
        ).fetchone()[0]
    assert audit is not None
    assert audit[0].startswith("gateway-denial-")
    assert audit[0] != request.idempotency_key
    assert audit[1:] == ("deny", "invalid_amount")
    assert caller_key_attempts == 0

    gateway.principal_provider = trusted_provider
    retry = gateway.execute(replace(request, direct_spend_usd=0))
    assert retry.allowed is True
    assert retry.status == "verified"


def test_malformed_request_is_audited_without_reserving_caller_key(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    gateway = _make_gateway(database_path, public_key, SimulatedExternalTool([]))
    trusted_provider = gateway.principal_provider

    class ActionId(str):
        pass

    request = replace(
        _execution_request(approval, idempotency_key="malformed-shape-key-001"),
        action_id=ActionId("publish_listing"),
    )
    provider_calls = []

    def unauthenticated_provider(_request):
        provider_calls.append("called")
        raise RuntimeError("no authenticated principal")

    gateway.principal_provider = unauthenticated_provider
    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "invalid_action_id"
    assert outcome.attempt_id is None
    assert provider_calls == []
    with sqlite3.connect(database_path) as connection:
        audit = connection.execute(
            """SELECT idempotency_key, decision, reason, principal_id
               FROM execution_attempts WHERE reason = 'invalid_action_id'"""
        ).fetchone()
    assert audit is not None
    assert audit[0].startswith("gateway-denial-")
    assert audit[0] != request.idempotency_key
    assert audit[1:] == ("deny", "invalid_action_id", "unknown")

    gateway.principal_provider = trusted_provider
    valid_retry = gateway.execute(replace(request, action_id=approval.approved_action))
    assert valid_retry.allowed is True
    assert valid_retry.status == "verified"


def test_simulator_rejects_action_id_with_overridden_format(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    ApprovalStore(database_path).add_approval(approval)
    side_effects = []

    class SideEffectString(str):
        def __format__(self, format_spec):
            side_effects.append(format_spec)
            return super().__format__(format_spec)

    request = replace(
        _execution_request(approval, idempotency_key="str-subclass-action-001"),
        action_id=SideEffectString("publish_listing"),
    )
    outcome = _make_gateway(
        database_path, public_key, SimulatedExternalTool([])
    ).execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "invalid_action_id"
    assert side_effects == []

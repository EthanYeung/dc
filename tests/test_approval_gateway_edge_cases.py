import sqlite3
from dataclasses import replace
from types import MappingProxyType

import pytest
from test_approval_gateway import (
    _execution_request,
    _key_pair,
    _make_database,
    _make_gateway,
    _make_internal_gateway,
    _signed_approval,
)

from runtime.approval_gateway import (
    ExecutionRequest,
    KillSwitch,
    SimulatedExternalTool,
    ToolResult,
)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("idempotency_key", "invalid_idempotency_key"),
        ("actor_role", "invalid_actor_role"),
        ("action_id", "invalid_action_id"),
        ("worker_run_id", "invalid_worker_run_id"),
        ("approval_id", "invalid_approval_id"),
        ("experiment_id", "invalid_experiment_id"),
        ("offer_id", "invalid_offer_id"),
        ("channel_id", "invalid_channel_id"),
    ],
)
def test_surrogate_text_fields_are_rejected_with_detached_audit(
    tmp_path, field, reason
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    gateway = _make_gateway(
        database_path, public_key, SimulatedExternalTool([])
    )
    trusted_provider = gateway.principal_provider
    provider_calls = []

    def tracked_provider(request):
        provider_calls.append(request.action_id)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    caller_key = "surrogate-text-field-001"
    request = replace(
        _execution_request(approval, idempotency_key=caller_key),
        **{field: "invalid-" + chr(0xD800)},
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
            (caller_key,),
        ).fetchone()[0]
    assert denial is not None
    assert denial[0].startswith("gateway-denial-")
    assert denial[1:] == ("deny", reason)
    assert caller_key_attempts == 0


@pytest.mark.parametrize("failure_status", ["tool_error", "verification_failed"])
def test_failed_authorized_execution_replay_preserves_allowed_semantics(
    tmp_path, failure_status
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    calls = []

    def internal_tool(request: ExecutionRequest) -> ToolResult:
        calls.append(request.action_id)
        if failure_status == "tool_error":
            raise RuntimeError("fixture failure")
        return ToolResult(request.action_id, None, "invalid=reference", True, True)

    gateway = _make_internal_gateway(database_path, internal_tool)
    request = ExecutionRequest(
        idempotency_key=f"failed-replay-{failure_status}",
        actor_role="builder",
        worker_run_id="run-failed-replay",
        action_id="internal.run_tests",
        payload={},
    )

    first = gateway.execute(request)
    replay = gateway.execute(request)

    assert first.allowed is True
    assert first.status == failure_status
    assert replay.allowed is True
    assert replay.status == failure_status
    assert replay.result is None
    assert calls == ["internal.run_tests"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("idempotency_key", "invalid_idempotency_key"),
        ("actor_role", "invalid_actor_role"),
        ("action_id", "invalid_action_id"),
        ("worker_run_id", "invalid_worker_run_id"),
        ("approval_id", "invalid_approval_id"),
        ("experiment_id", "invalid_experiment_id"),
        ("offer_id", "invalid_offer_id"),
        ("channel_id", "invalid_channel_id"),
    ],
)
def test_oversized_request_text_is_rejected_before_authentication(
    tmp_path, field, reason
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    gateway = _make_gateway(
        database_path, public_key, SimulatedExternalTool([])
    )
    trusted_provider = gateway.principal_provider
    provider_calls = []

    def tracked_provider(request):
        provider_calls.append(request.action_id)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    caller_key = "oversized-request-text-001"
    oversized = " " + "x" * 100_000
    request = replace(
        _execution_request(approval, idempotency_key=caller_key),
        **{field: oversized},
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
            (caller_key,),
        ).fetchone()[0]
    assert denial is not None
    assert denial[0].startswith("gateway-denial-")
    assert denial[1:] == ("deny", reason)
    assert caller_key_attempts == 0


def test_aggregate_request_metadata_budget_is_enforced_before_authentication(
    tmp_path,
):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    private_key, public_key = _key_pair()
    approval = _signed_approval(private_key)
    gateway = _make_gateway(
        database_path, public_key, SimulatedExternalTool([])
    )
    trusted_provider = gateway.principal_provider
    provider_calls = []

    def tracked_provider(request):
        provider_calls.append(request.action_id)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    caller_key = "aggregate-metadata-budget-001"
    large_unicode_field = "😀" * 256
    request = replace(
        _execution_request(approval, idempotency_key=caller_key),
        worker_run_id=large_unicode_field,
        approval_id=large_unicode_field,
        experiment_id=large_unicode_field,
        offer_id=large_unicode_field,
        channel_id=large_unicode_field,
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "request_text_budget_exceeded"
    assert outcome.attempt_id is None
    assert provider_calls == []
    with sqlite3.connect(database_path) as connection:
        denial = connection.execute(
            "SELECT idempotency_key, decision, reason FROM execution_attempts "
            "WHERE reason = 'request_text_budget_exceeded'"
        ).fetchone()
        caller_key_attempts = connection.execute(
            "SELECT COUNT(*) FROM execution_attempts WHERE idempotency_key = ?",
            (caller_key,),
        ).fetchone()[0]
    assert denial is not None
    assert denial[0].startswith("gateway-denial-")
    assert denial[1:] == ("deny", "request_text_budget_exceeded")
    assert caller_key_attempts == 0


def test_mappingproxy_over_custom_dict_is_rejected_without_callbacks(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    handler_calls = []

    def internal_handler(request):
        handler_calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:unexpected", True, True)

    gateway = _make_internal_gateway(database_path, internal_handler)
    trusted_provider = gateway.principal_provider
    provider_calls = []

    def tracked_provider(request):
        provider_calls.append(request.action_id)
        return trusted_provider(request)

    gateway.principal_provider = tracked_provider
    callback_calls = []

    class HostileDict(dict):
        def items(self):
            callback_calls.append("items")
            raise RuntimeError("user-defined mapping callback executed")

    caller_key = "proxy-custom-mapping-001"
    request = ExecutionRequest(
        idempotency_key=caller_key,
        actor_role="builder",
        worker_run_id="run-proxy-custom-mapping",
        action_id="internal.run_tests",
        payload=MappingProxyType(HostileDict({"safe": "value"})),
    )

    outcome = gateway.execute(request)

    assert outcome.allowed is False
    assert outcome.reason == "invalid_request_payload"
    assert outcome.attempt_id is None
    assert callback_calls == []
    assert provider_calls == []
    assert handler_calls == []
    with sqlite3.connect(database_path) as connection:
        denial = connection.execute(
            "SELECT idempotency_key, decision, reason FROM execution_attempts "
            "WHERE reason = 'invalid_request_payload'"
        ).fetchone()
        caller_key_attempts = connection.execute(
            "SELECT COUNT(*) FROM execution_attempts WHERE idempotency_key = ?",
            (caller_key,),
        ).fetchone()[0]
    assert denial is not None
    assert denial[0].startswith("gateway-denial-")
    assert denial[1:] == ("deny", "invalid_request_payload")
    assert caller_key_attempts == 0


def test_prebind_kill_switch_activation_is_persisted_when_gateway_binds(tmp_path):
    database_path = tmp_path / "gateway.db"
    _make_database(database_path)
    with sqlite3.connect(database_path) as connection:
        initial_state = connection.execute(
            "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
            ("global",),
        ).fetchone()[0]
    assert initial_state == 0

    kill_switch = KillSwitch()
    kill_switch.activate()
    assert kill_switch.is_active() is True
    handler_calls = []

    def internal_handler(request):
        handler_calls.append(request.action_id)
        return ToolResult(request.action_id, None, "internal:unexpected", True, True)

    gateway = _make_internal_gateway(
        database_path, internal_handler, kill_switch=kill_switch
    )

    assert kill_switch.is_active() is True
    with sqlite3.connect(database_path) as connection:
        persisted_state = connection.execute(
            "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
            ("global",),
        ).fetchone()[0]
    assert persisted_state == 1

    outcome = gateway.execute(
        ExecutionRequest(
            idempotency_key="prebind-kill-switch-001",
            actor_role="builder",
            worker_run_id="run-prebind-kill-switch",
            action_id="internal.run_tests",
            payload={},
        )
    )

    assert outcome.allowed is False
    assert outcome.reason == "kill_switch_active"
    assert handler_calls == []

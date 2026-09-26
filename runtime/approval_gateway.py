"""Signed approval verification and fail-closed simulated execution gateway.

External bindings are simulation-only in this first implementation. A trusted
application bootstrap must own the binding registry; worker requests select only
canonical action IDs and never provide callables.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import sqlite3
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, fields, replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from threading import Lock
from types import MappingProxyType
from typing import Protocol, cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from policy_engine.engine import (
    FOUNDER_APPROVAL_ACTIONS,
    ActionRequest,
    evaluate_action,
)
from policy_engine.exposure import ExposureRequest, assess_exposure

UTC = timezone.utc  # noqa: UP017  # Keep compatibility with Python 3.10.
_MAPPING_PROXY_TYPE = type(MappingProxyType({}))
MAX_REQUEST_PAYLOAD_BYTES = 64 * 1024
MAX_REQUEST_PAYLOAD_CANONICAL_BYTES = 256 * 1024
MAX_REQUEST_PAYLOAD_ITEMS = 4096
MAX_REQUEST_PAYLOAD_DEPTH = 32
MAX_REQUEST_PAYLOAD_INTEGER_BITS = 256
MAX_REQUEST_METADATA_TEXT_BYTES = 4 * 1024
MAX_AMOUNT_EXPONENT = 128
MAX_AMOUNT_PRECISION = 256
MAX_AMOUNT_ADJUSTED_EXPONENT = 128
_MAX_INTEGER_AMOUNT = 10**MAX_AMOUNT_ADJUSTED_EXPONENT
INTERNAL_ACTION_IDS = frozenset(
    {
        "internal.public_research",
        "internal.local_code_change",
        "internal.run_tests",
        "internal.git_artifact",
        "internal.read_only_state_inspection",
        "internal.non_consequential_analysis",
    }
)
EXTERNAL_ACTION_IDS = frozenset(FOUNDER_APPROVAL_ACTIONS | {"record_payout_state"})
TRUSTED_WORKER_ROLES = frozenset({"allocator", "research", "builder", "growth", "auditor"})


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_timestamp(value: object) -> datetime:
    if type(value) is not str or not value:
        raise ValueError("timestamp must be non-empty text")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    normalized = parsed.astimezone(UTC)
    if value != _utc_iso(normalized):
        raise ValueError("timestamp must use canonical UTC second precision")
    return normalized


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _exposure_payload(exposure: ExposureRequest) -> dict[str, object]:
    values = {item.name: getattr(exposure, item.name) for item in fields(ExposureRequest)}
    values["risk_flags"] = sorted(exposure.risk_flags)
    return values


def _exposure_from_payload(value: object) -> ExposureRequest:
    if not isinstance(value, dict):
        raise TypeError("approval exposure must be an object")
    data = dict(value)
    risk_flags = data.get("risk_flags")
    if not isinstance(risk_flags, list) or any(not isinstance(flag, str) for flag in risk_flags):
        raise ValueError("approval risk flags must be a list of strings")
    data["risk_flags"] = frozenset(risk_flags)
    return ExposureRequest(**data)


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    experiment_id: str
    approved_action: str
    approved_offer: str
    approved_channel: str
    risk_class: str
    exposure: ExposureRequest
    founder_decision: str
    decision_timestamp: datetime
    expires_at: datetime
    evidence_refs: tuple[str, ...]
    key_id: str
    signature_b64: str

    def signed_payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "approval_id": self.approval_id,
            "experiment_id": self.experiment_id,
            "approved_action": self.approved_action,
            "approved_offer": self.approved_offer,
            "approved_channel": self.approved_channel,
            "risk_class": self.risk_class,
            "exposure": _exposure_payload(self.exposure),
            "max_transactions": self.exposure.max_transactions,
            "max_transaction_value_usd": self.exposure.max_transaction_value_usd,
            "estimated_max_plausible_loss_usd": self.exposure.estimated_max_plausible_loss_usd,
            "max_direct_spend_usd": self.exposure.max_direct_spend_usd,
            "max_founder_attention_minutes": self.exposure.max_founder_attention_minutes,
            "max_delivery_labor_hours": self.exposure.max_delivery_labor_hours,
            "timebox_days": self.exposure.timebox_days,
            "max_channels": self.exposure.max_channels,
            "max_offers": self.exposure.max_offers,
            "founder_decision": self.founder_decision,
            "decision_timestamp": _utc_iso(self.decision_timestamp),
            "expires_at": _utc_iso(self.expires_at),
            "evidence_refs": list(self.evidence_refs),
            "key_id": self.key_id,
        }

    def signing_bytes(self) -> bytes:
        """Canonical bytes the offline Founder signer must sign with Ed25519."""
        return _canonical_json(self.signed_payload()).encode("utf-8")

    @classmethod
    def from_storage(
        cls,
        payload_json: str,
        signature_b64: str,
        stored_key_id: str,
    ) -> ApprovalRecord:
        payload = json.loads(payload_json)
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ValueError("unsupported approval record schema")
        evidence_refs = payload.get("evidence_refs")
        if not isinstance(evidence_refs, list) or any(
            not isinstance(ref, str) or not ref.strip() for ref in evidence_refs
        ):
            raise ValueError("approval evidence references are invalid")
        if payload.get("key_id") != stored_key_id:
            raise ValueError("approval key ID does not match storage index")
        exposure = _exposure_from_payload(payload["exposure"])
        duplicated_caps = {
            "max_transactions": exposure.max_transactions,
            "max_transaction_value_usd": exposure.max_transaction_value_usd,
            "estimated_max_plausible_loss_usd": exposure.estimated_max_plausible_loss_usd,
            "max_direct_spend_usd": exposure.max_direct_spend_usd,
            "max_founder_attention_minutes": exposure.max_founder_attention_minutes,
            "max_delivery_labor_hours": exposure.max_delivery_labor_hours,
            "timebox_days": exposure.timebox_days,
            "max_channels": exposure.max_channels,
            "max_offers": exposure.max_offers,
        }
        if any(payload.get(name) != value for name, value in duplicated_caps.items()):
            raise ValueError("approval cap index does not match policy snapshot")
        return cls(
            approval_id=payload["approval_id"],
            experiment_id=payload["experiment_id"],
            approved_action=payload["approved_action"],
            approved_offer=payload["approved_offer"],
            approved_channel=payload["approved_channel"],
            risk_class=payload["risk_class"],
            exposure=exposure,
            founder_decision=payload["founder_decision"],
            decision_timestamp=_parse_timestamp(payload["decision_timestamp"]),
            expires_at=_parse_timestamp(payload["expires_at"]),
            evidence_refs=tuple(evidence_refs),
            key_id=stored_key_id,
            signature_b64=signature_b64,
        )

    @property
    def max_transactions(self) -> int | None:
        return self.exposure.max_transactions

    @property
    def max_transaction_value_usd(self) -> float | None:
        return self.exposure.max_transaction_value_usd

    @property
    def max_direct_spend_usd(self) -> float | None:
        return self.exposure.max_direct_spend_usd

    @property
    def max_founder_attention_minutes(self) -> float | None:
        return self.exposure.max_founder_attention_minutes

    @property
    def max_delivery_labor_hours(self) -> float | None:
        return self.exposure.max_delivery_labor_hours

    @property
    def timebox_days(self) -> float | None:
        return self.exposure.timebox_days


class ApprovalVerifier:
    """Verify Founder signatures using public keys supplied by trusted bootstrap."""

    def __init__(self, public_keys: Mapping[str, bytes]):
        validated: dict[str, bytes] = {}
        for key_id, key_bytes in public_keys.items():
            if not isinstance(key_id, str) or not key_id.strip():
                raise ValueError("key IDs must be non-empty text")
            if not isinstance(key_bytes, bytes) or len(key_bytes) != 32:
                raise ValueError("Ed25519 public keys must be 32 raw bytes")
            validated[key_id] = key_bytes
        self._public_keys = MappingProxyType(validated)

    def verify(self, record: ApprovalRecord) -> tuple[bool, str]:
        if not isinstance(record.key_id, str):
            return False, "unknown_approval_key"
        public_bytes = self._public_keys.get(record.key_id)
        if public_bytes is None:
            return False, "unknown_approval_key"
        try:
            signature = base64.b64decode(record.signature_b64, validate=True)
            Ed25519PublicKey.from_public_bytes(public_bytes).verify(
                signature, record.signing_bytes()
            )
        except (InvalidSignature, ValueError, TypeError, binascii.Error):
            return False, "invalid_approval_signature"
        return True, "signature_valid"


class ApprovalStore:
    """SQLite persistence for signed approvals and immutable execution audit."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.database_path), timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_approval(self, record: ApprovalRecord) -> None:
        with self.transaction(immediate=True) as connection:
            connection.execute(
                """INSERT INTO approval_records
                   (approval_id, payload_json, signature_b64, key_id, received_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    record.approval_id,
                    _canonical_json(record.signed_payload()),
                    record.signature_b64,
                    record.key_id,
                    _utc_iso(datetime.now(UTC)),
                ),
            )

    def _load_approval(
        self, connection: sqlite3.Connection, approval_id: str
    ) -> ApprovalRecord | None:
        row = connection.execute(
            """SELECT payload_json, signature_b64, key_id
               FROM approval_records WHERE approval_id = ?""",
            (approval_id,),
        ).fetchone()
        if row is None:
            return None
        record = ApprovalRecord.from_storage(
            row["payload_json"], row["signature_b64"], row["key_id"]
        )
        if record.approval_id != approval_id:
            raise ValueError("approval ID does not match storage key")
        return record


@dataclass(frozen=True)
class ExecutionRequest:
    idempotency_key: str
    actor_role: str
    worker_run_id: str | None
    action_id: str
    approval_id: str | None = None
    experiment_id: str | None = None
    offer_id: str | None = None
    channel_id: str | None = None
    transaction_value_usd: int | float | Decimal = 0.0
    direct_spend_usd: int | float | Decimal = 0.0
    founder_attention_minutes: int | float | Decimal = 0.0
    delivery_labor_hours: int | float | Decimal = 0.0
    payload: Mapping[str, object] | None = None


@dataclass(frozen=True)
class NormalizedExecutionCommand:
    request: ExecutionRequest
    idempotency_key: str
    scope: str


@dataclass(frozen=True)
class TrustedPrincipal:
    """Authenticated caller identity returned by the trusted gateway boundary."""

    principal_id: str
    role: str
    worker_run_id: str | None


@dataclass(frozen=True)
class ToolResult:
    action_id: str
    approval_id: str | None
    external_ref: str
    verified: bool
    simulated: bool


class SimulatedExternalTool:
    """Built-in no-I/O result stub; external callables cannot be injected."""

    __slots__ = ("_calls", "_observer")

    def __init__(self, call_log: list[str] | None = None):
        if call_log is not None and type(call_log) is not list:
            raise TypeError("simulation call log must be a built-in list")
        self._calls: list[str] = []
        self._observer = call_log

    def has_safe_recording_state(self) -> bool:
        return type(self._calls) is list and (
            self._observer is None or type(self._observer) is list
        )

    def __call__(self, request: ExecutionRequest) -> ToolResult:
        if type(request) is not ExecutionRequest or type(request.action_id) is not str:
            raise RuntimeError("simulator requires a plain execution request")
        action_id = next(
            (allowed for allowed in EXTERNAL_ACTION_IDS if allowed == request.action_id),
            None,
        )
        if action_id is None:
            raise RuntimeError("simulator requires a registered external action")
        approval_id = request.approval_id
        if approval_id is not None and type(approval_id) is not str:
            raise RuntimeError("simulator requires a plain approval ID")
        calls = self._calls
        observer = self._observer
        if type(calls) is not list or (observer is not None and type(observer) is not list):
            raise RuntimeError("simulator recording state is invalid")
        list.append(calls, action_id)
        if observer is not None:
            list.append(observer, action_id)
        external_ref = "simulated:" + action_id + ":" + format(list.__len__(calls), "06d")
        return ToolResult(
            action_id=action_id,
            approval_id=approval_id,
            external_ref=external_ref,
            verified=True,
            simulated=True,
        )


@dataclass(frozen=True)
class ToolBinding:
    action_id: str
    scope: str
    handler: Callable[[ExecutionRequest], ToolResult] | None
    simulation_only: bool
    allowed_roles: frozenset[str] = frozenset()


class ToolBindingProvider(Protocol):
    def get(self, action_id: str) -> ToolBinding | None: ...


class ToolBindingRegistry:
    """Immutable trusted action-to-tool map; request data cannot add bindings."""

    def __init__(self, bindings: Iterable[ToolBinding]):
        registry: dict[str, ToolBinding] = {}
        for binding in bindings:
            if binding.action_id in registry:
                raise ValueError("duplicate canonical action binding")
            if binding.scope == "internal":
                if binding.action_id not in INTERNAL_ACTION_IDS:
                    raise ValueError("internal action is not in the trusted allowlist")
                if not callable(binding.handler):
                    raise ValueError("internal tool binding must contain a callable handler")
            elif binding.scope == "external":
                if binding.action_id not in EXTERNAL_ACTION_IDS:
                    raise ValueError("external action is not a canonical approval action")
                if binding.simulation_only is not True:
                    raise ValueError("live external tool bindings are disabled")
                handler = binding.handler
                if (
                    not isinstance(handler, SimulatedExternalTool)
                    or type(handler) is not SimulatedExternalTool
                    or not handler.has_safe_recording_state()
                ):
                    raise ValueError("external tool callables are disabled")
            else:
                raise ValueError("tool binding scope must be internal or external")
            if (
                not isinstance(binding.allowed_roles, frozenset)
                or not binding.allowed_roles
                or not binding.allowed_roles <= TRUSTED_WORKER_ROLES
            ):
                raise ValueError("tool binding must declare trusted worker roles")
            registry[binding.action_id] = binding
        self._bindings = MappingProxyType(registry)

    def get(self, action_id: object) -> ToolBinding | None:
        return self._bindings.get(action_id) if isinstance(action_id, str) else None


class KillSwitch:
    """Database-backed admission gate shared by gateways using one store."""

    def __init__(self, active: bool | None = None):
        if active is not None and not isinstance(active, bool):
            raise TypeError("kill switch state must be boolean")
        self._store: ApprovalStore | None = None
        self._initial_active = active
        self._pending_active = False
        self._lock = Lock()

    def bind(self, store: ApprovalStore) -> None:
        if not isinstance(store, ApprovalStore):
            raise TypeError("kill switch must bind to an ApprovalStore")
        with self._lock:
            if self._store is not None:
                if self._store.database_path.resolve() != store.database_path.resolve():
                    raise ValueError("kill switch cannot span different approval stores")
                return
            self._store = store
            pending_active = self._pending_active
            initial_active = self._initial_active
            try:
                with store.transaction(immediate=True) as connection:
                    row = connection.execute(
                        "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
                        ("global",),
                    ).fetchone()
                    if row is None:
                        active = pending_active or (
                            True if initial_active is None else initial_active
                        )
                        connection.execute(
                            "INSERT INTO gateway_control (control_id, kill_switch_active) "
                            "VALUES (?, ?)",
                            ("global", int(active)),
                        )
                    elif pending_active:
                        connection.execute(
                            """UPDATE gateway_control
                               SET kill_switch_active = 1, updated_at = CURRENT_TIMESTAMP
                               WHERE control_id = ?""",
                            ("global",),
                        )
                    # Existing state is authoritative unless explicitly activated pre-bind.
                self._initial_active = None
                self._pending_active = False
            except Exception:
                self._pending_active = True
                raise

    @staticmethod
    def _state_from_row(row: sqlite3.Row) -> bool:
        value = row["kill_switch_active"]
        return value not in (0, 1) or bool(value)

    def is_active(self, connection: sqlite3.Connection | None = None) -> bool:
        with self._lock:
            if self._pending_active:
                return True
            store = self._store
        if store is None:
            return True
        try:
            if connection is not None:
                row = connection.execute(
                    "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
                    ("global",),
                ).fetchone()
                return True if row is None else self._state_from_row(row)
            with store.transaction() as current:
                row = current.execute(
                    "SELECT kill_switch_active FROM gateway_control WHERE control_id = ?",
                    ("global",),
                ).fetchone()
                return True if row is None else self._state_from_row(row)
        except (sqlite3.Error, KeyError, IndexError, TypeError, ValueError):
            return True

    def activate(self) -> None:
        self._set_state(True)

    def deactivate(self) -> None:
        self._set_state(False)

    def _set_state(self, active: bool) -> None:
        with self._lock:
            store = self._store
            if active:
                self._pending_active = True
            if store is None:
                self._initial_active = active
                if not active:
                    self._pending_active = False
                return
        with store.transaction(immediate=True) as connection:
            connection.execute(
                """INSERT INTO gateway_control (control_id, kill_switch_active)
                   VALUES (?, ?)
                   ON CONFLICT(control_id) DO UPDATE SET
                       kill_switch_active = excluded.kill_switch_active,
                       updated_at = CURRENT_TIMESTAMP""",
                ("global", int(active)),
            )
        with self._lock:
            self._initial_active = None
            self._pending_active = False


@dataclass(frozen=True)
class ExecutionOutcome:
    """`allowed` means authorization passed, not that a tool succeeded."""

    allowed: bool
    status: str
    reason: str
    attempt_id: str | None
    result: ToolResult | None = None


def _decimal_amount(value: object) -> Decimal | None:
    if type(value) is int:
        if value > _MAX_INTEGER_AMOUNT or value < -_MAX_INTEGER_AMOUNT:
            return None
        amount = Decimal(value)
    elif type(value) is float:
        if not math.isfinite(value):
            return None
        amount = Decimal(str(value))
    elif type(value) is Decimal:
        amount = value
    else:
        return None
    if not amount.is_finite():
        return None
    parts = amount.as_tuple()
    if (
        type(parts.exponent) is not int
        or not -MAX_AMOUNT_EXPONENT <= parts.exponent <= MAX_AMOUNT_EXPONENT
        or len(parts.digits) > MAX_AMOUNT_PRECISION
        or amount.adjusted() > MAX_AMOUNT_ADJUSTED_EXPONENT
    ):
        return None
    return amount


def _amount_text(value: object) -> str:
    amount = _decimal_amount(value)
    return format(amount, "f") if amount is not None else "invalid"


def _amount_units(value: Decimal) -> int:
    parts = value.as_tuple()
    if (
        type(parts.exponent) is not int
        or not -MAX_AMOUNT_EXPONENT <= parts.exponent <= MAX_AMOUNT_EXPONENT
    ):
        raise ValueError("amount is outside the normalized exponent range")
    coefficient = 0
    for digit in parts.digits:
        coefficient = coefficient * 10 + digit
    units = coefficient * 10 ** (parts.exponent + MAX_AMOUNT_EXPONENT)
    return -units if parts.sign else units


def _stored_amount_units(value: object) -> int | None:
    try:
        parsed = _decimal_amount(Decimal(value)) if type(value) is str else _decimal_amount(value)
    except (ArithmeticError, TypeError, ValueError):
        return None
    return _amount_units(parsed) if parsed is not None else None


def _utf8_encodable(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _safe_text(value: object, *, fallback: str, limit: int = 256) -> str:
    if (
        type(value) is str
        and len(value) <= limit
        and value.strip()
        and _utf8_encodable(value)
    ):
        return value
    return fallback


def _valid_result_reference_format(value: object) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= 512
        and value.isascii()
        and all(char.isalnum() or char in "._:/-" for char in value)
    )


def _gateway_result_reference(attempt_id: str) -> str:
    return f"gateway-result:{attempt_id}"


@dataclass
class _PayloadCopyBudget:
    items: int = 0
    text_bytes: int = 0

    def add_item(self) -> None:
        self.items += 1
        if self.items > MAX_REQUEST_PAYLOAD_ITEMS:
            raise ValueError("payload item limit exceeded")

    def add_text(self, value: str) -> None:
        if len(value) > MAX_REQUEST_PAYLOAD_BYTES:
            raise ValueError("payload text limit exceeded")
        self.text_bytes += len(value.encode("utf-8"))
        if self.text_bytes > MAX_REQUEST_PAYLOAD_BYTES:
            raise ValueError("payload byte limit exceeded")


def _copy_json_payload(
    value: object,
    active: set[int] | None = None,
    *,
    depth: int = 0,
    budget: _PayloadCopyBudget | None = None,
) -> object:
    copy_budget = budget if budget is not None else _PayloadCopyBudget()
    if depth > MAX_REQUEST_PAYLOAD_DEPTH:
        raise ValueError("payload depth limit exceeded")
    copy_budget.add_item()
    if type(value) is str:
        copy_budget.add_text(value)
        return value
    if value is None or type(value) in (float, bool):
        return value
    if type(value) is int:
        if value.bit_length() > MAX_REQUEST_PAYLOAD_INTEGER_BITS:
            raise ValueError("payload integer limit exceeded")
        return value
    if type(value) is dict:
        mapping = cast(Mapping[object, object], value)
        seen = active if active is not None else set()
        identity = id(value)
        if identity in seen:
            raise ValueError("payload must not contain cycles")
        seen.add(identity)
        try:
            copied: dict[str, object] = {}
            for key, item in mapping.items():
                if type(key) is not str:
                    raise TypeError("payload keys must be plain strings")
                copy_budget.add_item()
                copy_budget.add_text(key)
                copied[key] = _copy_json_payload(
                    item, seen, depth=depth + 1, budget=copy_budget
                )
            return copied
        finally:
            seen.remove(identity)
    if type(value) in (list, tuple):
        sequence = cast(list[object] | tuple[object, ...], value)
        seen = active if active is not None else set()
        identity = id(value)
        if identity in seen:
            raise ValueError("payload must not contain cycles")
        seen.add(identity)
        try:
            copied_items = []
            for item in sequence:
                copied_items.append(
                    _copy_json_payload(
                        item, seen, depth=depth + 1, budget=copy_budget
                    )
                )
            return copied_items
        finally:
            seen.remove(identity)
    raise TypeError("payload must contain only JSON values")


def _freeze_json_payload(value: object) -> object:
    if type(value) is dict:
        return MappingProxyType(
            {key: _freeze_json_payload(item) for key, item in value.items()}
        )
    if type(value) is list:
        return tuple(_freeze_json_payload(item) for item in value)
    return value


def _thaw_json_payload(value: object) -> object:
    if value is None or type(value) in (str, int, float, bool):
        return value
    if type(value) in (dict, _MAPPING_PROXY_TYPE):
        mapping = cast(Mapping[object, object], value)
        copied: dict[str, object] = {}
        for key, item in mapping.items():
            if type(key) is not str:
                raise TypeError("payload keys must be plain strings")
            copied[key] = _thaw_json_payload(item)
        return copied
    if type(value) in (list, tuple):
        sequence = cast(list[object] | tuple[object, ...], value)
        return [_thaw_json_payload(item) for item in sequence]
    raise TypeError("payload must contain only JSON values")


def _request_digest(
    request: ExecutionRequest, principal: TrustedPrincipal | None
) -> str:
    payload = request.payload
    try:
        payload_json = _canonical_json(_thaw_json_payload(payload))
        payload_digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    except (TypeError, ValueError, RecursionError):
        payload_digest = "invalid-payload"
    values = {
        "idempotency_key_digest": hashlib.sha256(
            _safe_text(request.idempotency_key, fallback="invalid", limit=128).encode(
                "utf-8"
            )
        ).hexdigest(),
        "actor_role": _safe_text(request.actor_role, fallback="invalid"),
        "action_id": _safe_text(request.action_id, fallback="invalid"),
        "approval_id": _safe_text(request.approval_id, fallback=""),
        "experiment_id": _safe_text(request.experiment_id, fallback=""),
        "offer_id": _safe_text(request.offer_id, fallback=""),
        "channel_id": _safe_text(request.channel_id, fallback=""),
        "transaction_value_usd": _amount_text(request.transaction_value_usd),
        "direct_spend_usd": _amount_text(request.direct_spend_usd),
        "founder_attention_minutes": _amount_text(request.founder_attention_minutes),
        "delivery_labor_hours": _amount_text(request.delivery_labor_hours),
        "worker_run_id": _safe_text(request.worker_run_id, fallback=""),
        "authenticated_principal_id": (
            _safe_text(principal.principal_id, fallback="invalid")
            if principal is not None
            else "unavailable"
        ),
        "authenticated_role": principal.role if principal is not None else "unavailable",
        "authenticated_worker_run_id": (
            _safe_text(principal.worker_run_id, fallback="")
            if principal is not None
            else ""
        ),
        "payload_digest": payload_digest,
    }
    return hashlib.sha256(_canonical_json(values).encode("utf-8")).hexdigest()


class ExecutionGateway:
    """Verify authority, policy, exact binding, caps, and result before success."""

    def __init__(
        self,
        *,
        store: ApprovalStore,
        verifier: ApprovalVerifier,
        bindings: ToolBindingProvider,
        clock: Callable[[], datetime],
        kill_switch: KillSwitch,
        principal_provider: Callable[[ExecutionRequest], TrustedPrincipal],
    ):
        if not isinstance(kill_switch, KillSwitch):
            raise TypeError("kill switch must be a trusted KillSwitch")
        if not callable(principal_provider):
            raise TypeError("principal provider must be callable")
        self.store = store
        self.verifier = verifier
        self.bindings = bindings
        self.clock = clock
        self.kill_switch = kill_switch
        self.kill_switch.bind(store)
        self.principal_provider = principal_provider

    def _resolve_binding(
        self, action_id: str, scope: str, trusted_role: str
    ) -> tuple[ToolBinding | None, str | None]:
        try:
            binding = self.bindings.get(action_id)
        except Exception:  # noqa: BLE001 - binding failures fail closed.
            return None, "trusted_tool_binding_unavailable"
        if (
            type(binding) is not ToolBinding
            or binding.action_id != action_id
            or binding.scope != scope
        ):
            return None, "trusted_tool_binding_unavailable"
        if scope == "internal":
            if action_id not in INTERNAL_ACTION_IDS or not callable(binding.handler):
                return None, "trusted_tool_binding_unavailable"
        elif scope == "external":
            if action_id not in EXTERNAL_ACTION_IDS:
                return None, "trusted_tool_binding_unavailable"
            handler = binding.handler
            if (
                binding.simulation_only is not True
                or not isinstance(handler, SimulatedExternalTool)
                or type(handler) is not SimulatedExternalTool
                or not handler.has_safe_recording_state()
            ):
                return None, "live_external_tool_disabled"
        else:
            return None, "trusted_tool_binding_unavailable"
        if (
            not isinstance(binding.allowed_roles, frozenset)
            or not binding.allowed_roles
            or not binding.allowed_roles <= TRUSTED_WORKER_ROLES
        ):
            return None, "trusted_tool_binding_unavailable"
        if trusted_role not in binding.allowed_roles:
            return None, "role_not_permitted"
        return binding, None

    def execute(self, request: ExecutionRequest) -> ExecutionOutcome:
        attempt_id = uuid.uuid4().hex
        created_at = _utc_iso(datetime.now(UTC))
        command, normalization_error, collision_key = self._normalize_request(request)
        if command is None:
            return self._record_request_shape_denial(
                attempt_id,
                normalization_error or "invalid_request",
                created_at,
                source_idempotency_key=collision_key,
            )
        request = command.request
        idempotency_key = command.idempotency_key
        action_id = request.action_id
        scope = command.scope
        binding: ToolBinding | None = None
        trusted_principal: TrustedPrincipal | None = None

        with self.store.transaction(immediate=True) as connection:
            existing = connection.execute(
                """SELECT attempt_id, request_digest, decision, reason,
                          action_id, action_scope, approval_id, principal_id,
                          worker_run_id
                   FROM execution_attempts WHERE idempotency_key = ?""",
                (idempotency_key,),
            ).fetchone()

            trusted_principal, identity_error = self._trusted_principal(request)
            if identity_error:
                return self._record_detached_denial(
                    connection,
                    attempt_id,
                    existing["attempt_id"] if existing is not None else None,
                    idempotency_key,
                    request,
                    scope,
                    _request_digest(request, None),
                    created_at,
                    identity_error,
                    trusted_principal=None,
                )
            assert trusted_principal is not None

            def deny(reason: str) -> ExecutionOutcome:
                request_digest = _request_digest(request, trusted_principal)
                if existing is not None:
                    if (
                        existing["principal_id"] != trusted_principal.principal_id
                        or existing["worker_run_id"] != trusted_principal.worker_run_id
                    ):
                        return self._record_detached_denial(
                            connection,
                            attempt_id,
                            existing["attempt_id"],
                            idempotency_key,
                            request,
                            scope,
                            request_digest,
                            created_at,
                            reason,
                            trusted_principal=trusted_principal,
                        )
                    self._append_execution_event(
                        connection,
                        existing["attempt_id"],
                        idempotency_key,
                        "idempotent_replay_denied",
                        reason,
                        request_digest,
                        created_at,
                    )
                    return ExecutionOutcome(
                        False, "denied", reason, existing["attempt_id"]
                    )
                return self._record_denial(
                    connection,
                    attempt_id,
                    idempotency_key,
                    request,
                    scope,
                    request_digest,
                    created_at,
                    reason,
                    trusted_principal=trusted_principal,
                )

            if scope == "unknown":
                return deny("unregistered_action")

            request_digest = _request_digest(request, trusted_principal)
            trusted_role = trusted_principal.role
            if request.actor_role != trusted_role:
                return deny("actor_identity_mismatch")
            if self.kill_switch.is_active(connection):
                return deny("kill_switch_active")

            if existing is not None and (
                existing["principal_id"] != trusted_principal.principal_id
                or existing["worker_run_id"] != trusted_principal.worker_run_id
            ):
                return deny("idempotency_key_conflict")

            if existing is not None and existing["request_digest"] != request_digest:
                self._append_execution_event(
                    connection,
                    existing["attempt_id"],
                    idempotency_key,
                    "idempotency_key_conflict",
                    "idempotency_key_conflict",
                    request_digest,
                    created_at,
                )
                return ExecutionOutcome(
                    False,
                    "denied",
                    "idempotency_key_conflict",
                    existing["attempt_id"],
                )

            if scope == "internal":
                reason = self._authorize_internal(request, trusted_role)
                if reason:
                    return deny(reason)
                binding, reason = self._resolve_binding(action_id, scope, trusted_role)
                if reason:
                    return deny(reason)
                approval_reason = "trusted_internal_binding"
            else:
                exclude_attempt_id = (
                    existing["attempt_id"] if existing is not None else None
                )
                try:
                    reason = self._authorize_external(
                        connection,
                        request,
                        self._current_time(),
                        trusted_role,
                        exclude_attempt_id=exclude_attempt_id,
                    )
                except Exception:  # noqa: BLE001 - malformed records must deny and audit.
                    reason = "approval_validation_error"
                if reason:
                    return deny(reason)
                binding, reason = self._resolve_binding(action_id, scope, trusted_role)
                if reason:
                    return deny(reason)
                approval_reason = "founder_approval_verified"

            if existing is not None:
                final_principal, final_identity_error = self._trusted_principal(request)
                if final_identity_error or final_principal != trusted_principal:
                    return deny("actor_identity_changed")
                if scope == "external":
                    try:
                        reason = self._authorize_external(
                            connection,
                            request,
                            self._current_time(),
                            trusted_role,
                            check_policy=False,
                            check_caps=False,
                        )
                    except Exception:  # noqa: BLE001 - replay revalidation fails closed.
                        reason = "approval_validation_error"
                    if reason:
                        return deny(reason)
                if self.kill_switch.is_active(connection):
                    return deny("kill_switch_active")
                replay_outcome = self._existing_outcome(connection, existing)
                self._append_execution_event(
                    connection,
                    existing["attempt_id"],
                    idempotency_key,
                    "idempotent_replay",
                    replay_outcome.reason,
                    request_digest,
                    created_at,
                )
                return replay_outcome

            self._insert_attempt(
                connection,
                attempt_id,
                idempotency_key,
                request,
                scope,
                "allow",
                approval_reason,
                request_digest,
                created_at,
                principal_id=trusted_principal.principal_id,
            )
            self._append_execution_event(
                connection,
                attempt_id,
                idempotency_key,
                "execution_reserved",
                "handler_invocation_reserved",
                request_digest,
                created_at,
            )

        if binding is None or trusted_principal is None:
            return ExecutionOutcome(
                False, "denied", "trusted_tool_binding_unavailable", attempt_id
            )

        with self.store.transaction(immediate=True) as connection:
            if self.kill_switch.is_active(connection):
                reason = "kill_switch_active"
                self._append_execution_event(
                    connection,
                    attempt_id,
                    idempotency_key,
                    "execution_blocked",
                    reason,
                    request_digest,
                    _utc_iso(datetime.now(UTC)),
                )
                return ExecutionOutcome(False, "denied", reason, attempt_id)
            final_principal, identity_error = self._trusted_principal(request)
            if identity_error or final_principal != trusted_principal:
                reason = "actor_identity_changed"
                self._append_execution_event(
                    connection,
                    attempt_id,
                    idempotency_key,
                    "execution_blocked",
                    reason,
                    request_digest,
                    _utc_iso(datetime.now(UTC)),
                )
                return ExecutionOutcome(False, "denied", reason, attempt_id)
            if scope == "external":
                try:
                    reason = self._authorize_external(
                        connection,
                        request,
                        self._current_time(),
                        trusted_principal.role,
                        check_policy=False,
                        check_caps=False,
                    )
                except Exception:  # noqa: BLE001 - final approval check fails closed.
                    reason = "approval_validation_error"
                if reason:
                    self._append_execution_event(
                        connection,
                        attempt_id,
                        idempotency_key,
                        "execution_blocked",
                        reason,
                        request_digest,
                        _utc_iso(datetime.now(UTC)),
                    )
                    return ExecutionOutcome(False, "denied", reason, attempt_id)
            final_binding, binding_error = self._resolve_binding(
                action_id, scope, trusted_principal.role
            )
            if binding_error or final_binding is None:
                reason = binding_error or "trusted_tool_binding_unavailable"
                self._append_execution_event(
                    connection,
                    attempt_id,
                    idempotency_key,
                    "execution_blocked",
                    reason,
                    request_digest,
                    _utc_iso(datetime.now(UTC)),
                )
                return ExecutionOutcome(False, "denied", reason, attempt_id)
            binding = final_binding
            self._append_execution_event(
                connection,
                attempt_id,
                idempotency_key,
                "execution_admitted",
                "handler_invocation_admitted",
                request_digest,
                _utc_iso(datetime.now(UTC)),
            )
        return self._invoke_tool(binding, request, attempt_id)

    @staticmethod
    def _append_idempotency_collision_relation(
        connection: sqlite3.Connection,
        denial_attempt_id: str,
        target_attempt_id: str,
        idempotency_key: str,
        created_at: str,
    ) -> None:
        connection.execute(
            """INSERT INTO execution_attempt_relations
               (relation_id, denial_attempt_id, relation_type,
                target_attempt_digest, idempotency_key_digest, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                uuid.uuid4().hex,
                denial_attempt_id,
                "idempotency_collision",
                hashlib.sha256(target_attempt_id.encode("utf-8")).hexdigest(),
                hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest(),
                created_at,
            ),
        )

    def _record_detached_denial(
        self,
        connection: sqlite3.Connection,
        denial_attempt_id: str,
        target_attempt_id: str | None,
        idempotency_key: str,
        request: ExecutionRequest,
        scope: str,
        request_digest: str,
        created_at: str,
        reason: str,
        *,
        trusted_principal: TrustedPrincipal | None,
    ) -> ExecutionOutcome:
        self._record_denial(
            connection,
            denial_attempt_id,
            f"gateway-denial-{denial_attempt_id}",
            request,
            scope,
            request_digest,
            created_at,
            reason,
            trusted_principal=trusted_principal,
        )
        if target_attempt_id is not None:
            self._append_idempotency_collision_relation(
                connection,
                denial_attempt_id,
                target_attempt_id,
                idempotency_key,
                created_at,
            )
        return ExecutionOutcome(False, "denied", reason, None)

    def _record_request_shape_denial(
        self,
        attempt_id: str,
        reason: str,
        created_at: str,
        *,
        source_idempotency_key: str | None,
    ) -> ExecutionOutcome:
        idempotency_key = f"gateway-denial-{attempt_id}"
        safe_request = ExecutionRequest(
            idempotency_key=idempotency_key,
            actor_role="unknown",
            worker_run_id=None,
            action_id="invalid_request",
        )
        request_digest = hashlib.sha256(
            f"request-shape:{reason}".encode()
        ).hexdigest()
        with self.store.transaction(immediate=True) as connection:
            target = None
            if source_idempotency_key is not None:
                target = connection.execute(
                    "SELECT attempt_id FROM execution_attempts WHERE idempotency_key = ?",
                    (source_idempotency_key,),
                ).fetchone()
            self._record_denial(
                connection,
                attempt_id,
                idempotency_key,
                safe_request,
                "unknown",
                request_digest,
                created_at,
                reason,
            )
            if target is not None and source_idempotency_key is not None:
                self._append_idempotency_collision_relation(
                    connection,
                    attempt_id,
                    target["attempt_id"],
                    source_idempotency_key,
                    created_at,
                )
        return ExecutionOutcome(False, "denied", reason, None)

    @staticmethod
    def _append_execution_event(
        connection: sqlite3.Connection,
        attempt_id: str,
        idempotency_key: str,
        event_type: str,
        reason: str,
        request_digest: str,
        created_at: str,
    ) -> None:
        connection.execute(
            """INSERT INTO execution_events
               (event_id, attempt_id, idempotency_key, event_type, reason,
                request_digest, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                uuid.uuid4().hex,
                attempt_id,
                idempotency_key,
                event_type,
                reason,
                request_digest,
                created_at,
            ),
        )

    def _trusted_principal(
        self, request: ExecutionRequest
    ) -> tuple[TrustedPrincipal | None, str | None]:
        try:
            principal = self.principal_provider(request)
        except Exception:  # noqa: BLE001 - identity failures fail closed.
            return None, "trusted_identity_unavailable"
        if type(principal) is not TrustedPrincipal:
            return None, "trusted_identity_unavailable"
        if (
            not _safe_text(principal.principal_id, fallback="", limit=256)
            or type(principal.role) is not str
            or principal.role not in TRUSTED_WORKER_ROLES
            or (
                principal.worker_run_id is not None
                and type(principal.worker_run_id) is not str
            )
        ):
            return None, "trusted_identity_unavailable"
        if principal.worker_run_id != request.worker_run_id:
            return None, "worker_run_identity_mismatch"
        return principal, None

    def _record_execution_event(
        self,
        attempt_id: str,
        request: ExecutionRequest,
        event_type: str,
        reason: str,
    ) -> bool:
        del request  # Event identity comes from the immutable reserved attempt.
        try:
            with self.store.transaction(immediate=True) as connection:
                row = connection.execute(
                    """SELECT idempotency_key, request_digest
                       FROM execution_attempts WHERE attempt_id = ?""",
                    (attempt_id,),
                ).fetchone()
                if row is None:
                    return False
                self._append_execution_event(
                    connection,
                    attempt_id,
                    row["idempotency_key"],
                    event_type,
                    reason,
                    row["request_digest"],
                    _utc_iso(datetime.now(UTC)),
                )
        except Exception:  # noqa: BLE001 - reserved event remains the durable fallback.
            return False
        return True

    def _save_result_safely(
        self,
        attempt_id: str,
        request: ExecutionRequest,
        status: str,
        result: dict[str, object],
    ) -> bool:
        try:
            self._save_result(attempt_id, status, result)
        except Exception:  # noqa: BLE001 - never retry a possibly executed handler.
            self._record_execution_event(
                attempt_id,
                request,
                "result_persistence_failed",
                "result_persistence_failed",
            )
            return False
        return True

    def _current_time(self) -> datetime | None:
        try:
            value = self.clock()
            if value.tzinfo is None or value.utcoffset() is None:
                return None
            return value.astimezone(UTC)
        except Exception:  # noqa: BLE001 - clock failure must fail closed.
            return None

    @staticmethod
    def _safe_collision_key(request: object) -> str | None:
        if type(request) is not ExecutionRequest:
            return None
        value = request.idempotency_key
        if type(value) is str and _safe_text(value, fallback="", limit=128):
            return value
        return None

    @staticmethod
    def _normalize_request(
        request: object,
    ) -> tuple[NormalizedExecutionCommand | None, str | None, str | None]:
        if type(request) is not ExecutionRequest:
            return None, "invalid_request_type", None
        request = replace(request)
        collision_key = ExecutionGateway._safe_collision_key(request)
        required_fields = (
            ("idempotency_key", "invalid_idempotency_key"),
            ("actor_role", "invalid_actor_role"),
            ("action_id", "invalid_action_id"),
        )
        for field, reason in required_fields:
            value = getattr(request, field)
            limit = 128 if field == "idempotency_key" else 256
            if type(value) is not str or not _safe_text(
                value, fallback="", limit=limit
            ):
                return None, reason, collision_key
        optional_fields = (
            ("worker_run_id", "invalid_worker_run_id"),
            ("approval_id", "invalid_approval_id"),
            ("experiment_id", "invalid_experiment_id"),
            ("offer_id", "invalid_offer_id"),
            ("channel_id", "invalid_channel_id"),
        )
        for field, reason in optional_fields:
            value = getattr(request, field)
            if value is not None and (
                type(value) is not str
                or len(value) > 256
                or not _utf8_encodable(value)
            ):
                return None, reason, collision_key
            if field == "worker_run_id" and value is not None and not _safe_text(
                value, fallback="", limit=256
            ):
                return None, reason, collision_key

        metadata_text_bytes = 0
        for field, _ in (*required_fields, *optional_fields):
            value = getattr(request, field)
            if value is not None:
                metadata_text_bytes += len(value.encode("utf-8"))
                if metadata_text_bytes > MAX_REQUEST_METADATA_TEXT_BYTES:
                    return None, "request_text_budget_exceeded", collision_key

        if request.action_id in INTERNAL_ACTION_IDS:
            scope = "internal"
        elif request.action_id in EXTERNAL_ACTION_IDS:
            scope = "external"
        else:
            scope = "unknown"
        if scope == "external":
            required_scope_fields = (
                ("offer_id", "invalid_offer_id"),
                ("channel_id", "invalid_channel_id"),
            )
            for field, reason in required_scope_fields:
                if not _safe_text(getattr(request, field), fallback="", limit=256):
                    return None, reason, collision_key

        amount_fields = (
            "transaction_value_usd",
            "direct_spend_usd",
            "founder_attention_minutes",
            "delivery_labor_hours",
        )
        normalized_amounts: dict[str, Decimal] = {}
        for field in amount_fields:
            value = getattr(request, field)
            if type(value) not in (int, float, Decimal):
                return None, "invalid_amount", collision_key
            amount = _decimal_amount(value)
            if amount is None or amount < 0:
                return None, "invalid_amount", collision_key
            normalized_amounts[field] = amount

        payload: object = None
        if request.payload is not None:
            try:
                copied_payload = _copy_json_payload(request.payload)
                if type(copied_payload) is not dict:
                    return None, "invalid_request_payload", collision_key
                canonical_payload = _canonical_json(copied_payload).encode("utf-8")
                if len(canonical_payload) > MAX_REQUEST_PAYLOAD_CANONICAL_BYTES:
                    return None, "invalid_request_payload", collision_key
                payload = _freeze_json_payload(copied_payload)
            except (TypeError, ValueError, RecursionError, RuntimeError):
                return None, "invalid_request_payload", collision_key

        request_snapshot = replace(
            request,
            **normalized_amounts,
            payload=cast(Mapping[str, object] | None, payload),
        )
        return (
            NormalizedExecutionCommand(
                request_snapshot,
                request_snapshot.idempotency_key,
                scope,
            ),
            None,
            collision_key,
        )

    @staticmethod
    def _authorize_internal(
        request: ExecutionRequest, trusted_role: str
    ) -> str | None:
        if trusted_role not in TRUSTED_WORKER_ROLES:
            return "trusted_identity_unavailable"
        if request.actor_role != trusted_role:
            return "actor_identity_mismatch"
        if request.approval_id is not None:
            return "approval_not_applicable_to_internal_action"
        if request.transaction_value_usd != 0 or request.direct_spend_usd != 0:
            return "internal_action_cannot_commit_external_value"
        if (
            request.experiment_id is not None
            or request.offer_id is not None
            or request.channel_id is not None
            or request.founder_attention_minutes != 0
            or request.delivery_labor_hours != 0
        ):
            return "internal_action_cannot_claim_experiment_usage"
        return None

    def _authorize_external(
        self,
        connection: sqlite3.Connection,
        request: ExecutionRequest,
        now: datetime | None,
        trusted_role: str,
        *,
        check_policy: bool = True,
        check_caps: bool = True,
        exclude_attempt_id: str | None = None,
    ) -> str | None:
        if now is None:
            return "gateway_clock_unavailable"
        try:
            approval = self.store._load_approval(connection, request.approval_id or "")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return "invalid_approval_record"
        if approval is None:
            return "missing_approval_record"

        signature_valid, signature_reason = self.verifier.verify(approval)
        if not signature_valid:
            return signature_reason
        approval_scope_fields = (
            approval.approval_id,
            approval.experiment_id,
            approval.approved_action,
            approval.approved_offer,
            approval.approved_channel,
        )
        if any(
            not _safe_text(value, fallback="", limit=256)
            for value in approval_scope_fields
        ):
            return "invalid_approval_scope"
        if approval.founder_decision != "approved":
            return "founder_decision_not_approved"
        if not approval.evidence_refs:
            return "approval_missing_evidence"
        if (
            approval.approval_id != request.approval_id
            or approval.experiment_id != request.experiment_id
            or approval.approved_action != request.action_id
            or approval.approved_offer != request.offer_id
            or approval.approved_channel != request.channel_id
            or approval.exposure.experiment_id != approval.experiment_id
        ):
            return "approval_scope_mismatch"
        if approval.risk_class == "C":
            return "class_c_prohibited"
        if approval.risk_class not in {"A", "B"}:
            return "invalid_risk_class"
        if approval.decision_timestamp > now or approval.expires_at <= now:
            return "approval_expired_or_not_yet_valid"
        timebox_days = _decimal_amount(approval.exposure.timebox_days)
        if timebox_days is None or timebox_days <= 0:
            return "invalid_approval_timebox"
        allowed_seconds = timebox_days * Decimal(86400)
        approved_seconds = Decimal(
            str((approval.expires_at - approval.decision_timestamp).total_seconds())
        )
        elapsed_seconds = Decimal(
            str((now - approval.decision_timestamp).total_seconds())
        )
        if approved_seconds <= 0 or approved_seconds > allowed_seconds:
            return "approval_exceeds_timebox"
        if elapsed_seconds > allowed_seconds:
            return "approval_timebox_exceeded"

        assessment = assess_exposure(approval.exposure)
        if assessment.risk_class == "C":
            return "class_c_prohibited"
        if assessment.risk_class != approval.risk_class:
            return "risk_class_mismatch"
        if not assessment.eligible_for_founder_review:
            return "exposure_not_reviewable"
        if approval.exposure.max_channels != 1 or approval.exposure.max_offers != 1:
            return "approval_scope_not_single_offer_channel"

        if check_policy:
            policy = evaluate_action(
                ActionRequest(
                    role=trusted_role,
                    action=request.action_id,
                    spend_usd=float(request.direct_spend_usd),
                    irreversible=True,
                )
            )
            if policy.reason != "founder_approval_required":
                return "policy_denied"

        if check_caps:
            cap_reason = self._check_caps(
                connection,
                request,
                approval,
                exclude_attempt_id=exclude_attempt_id,
            )
            if cap_reason:
                return cap_reason
        return None

    @staticmethod
    def _check_caps(
        connection: sqlite3.Connection,
        request: ExecutionRequest,
        approval: ApprovalRecord,
        *,
        exclude_attempt_id: str | None = None,
    ) -> str | None:
        exposure = approval.exposure
        transaction = _decimal_amount(request.transaction_value_usd)
        direct_spend = _decimal_amount(request.direct_spend_usd)
        attention = _decimal_amount(request.founder_attention_minutes)
        labor = _decimal_amount(request.delivery_labor_hours)
        transaction_cap = _decimal_amount(exposure.max_transaction_value_usd)
        spend_cap = _decimal_amount(exposure.max_direct_spend_usd)
        attention_cap = _decimal_amount(exposure.max_founder_attention_minutes)
        labor_cap = _decimal_amount(exposure.max_delivery_labor_hours)
        if (
            transaction is None
            or direct_spend is None
            or attention is None
            or labor is None
            or transaction_cap is None
            or spend_cap is None
            or attention_cap is None
            or labor_cap is None
        ):
            return "invalid_approval_cap"
        transaction_units = _amount_units(transaction)
        direct_spend_units = _amount_units(direct_spend)
        attention_units = _amount_units(attention)
        labor_units = _amount_units(labor)
        transaction_cap_units = _amount_units(transaction_cap)
        spend_cap_units = _amount_units(spend_cap)
        attention_cap_units = _amount_units(attention_cap)
        labor_cap_units = _amount_units(labor_cap)
        if transaction_units > transaction_cap_units:
            return "transaction_value_cap_exceeded"
        max_transactions = exposure.max_transactions
        if (
            not isinstance(max_transactions, int)
            or isinstance(max_transactions, bool)
            or max_transactions <= 0
        ):
            return "invalid_transaction_limit"

        approval_rows = connection.execute(
            """SELECT transaction_value_usd FROM execution_attempts
               WHERE approval_id = ? AND action_scope = 'external'
                 AND decision = 'allow'
                 AND (? IS NULL OR attempt_id != ?)""",
            (approval.approval_id, exclude_attempt_id, exclude_attempt_id),
        ).fetchall()
        if len(approval_rows) >= max_transactions:
            return "transaction_count_cap_exceeded"
        transaction_total_units = 0
        for row in approval_rows:
            row_units = _stored_amount_units(row["transaction_value_usd"])
            if row_units is None:
                return "invalid_execution_amount"
            transaction_total_units += row_units
        total_transaction_cap_units = transaction_cap_units * max_transactions
        if transaction_total_units + transaction_units > total_transaction_cap_units:
            return "transaction_value_cap_exceeded"

        experiment_rows = connection.execute(
            """SELECT direct_spend_usd, founder_attention_minutes, delivery_labor_hours
               FROM execution_attempts
               WHERE experiment_id = ? AND action_scope = 'external'
                 AND approval_id IS NOT NULL AND decision = 'allow'
                 AND (? IS NULL OR attempt_id != ?)""",
            (approval.experiment_id, exclude_attempt_id, exclude_attempt_id),
        ).fetchall()
        used_spend_units = 0
        used_attention_units = 0
        used_labor_units = 0
        for row in experiment_rows:
            row_spend_units = _stored_amount_units(row["direct_spend_usd"])
            row_attention_units = _stored_amount_units(row["founder_attention_minutes"])
            row_labor_units = _stored_amount_units(row["delivery_labor_hours"])
            if (
                row_spend_units is None
                or row_attention_units is None
                or row_labor_units is None
            ):
                return "invalid_execution_amount"
            used_spend_units += row_spend_units
            used_attention_units += row_attention_units
            used_labor_units += row_labor_units
        if used_spend_units + direct_spend_units > spend_cap_units:
            return "direct_spend_cap_exceeded"
        if used_attention_units + attention_units > attention_cap_units:
            return "founder_attention_cap_exceeded"
        if used_labor_units + labor_units > labor_cap_units:
            return "delivery_labor_cap_exceeded"
        return None

    @staticmethod
    def _insert_attempt(
        connection: sqlite3.Connection,
        attempt_id: str,
        idempotency_key: str,
        request: ExecutionRequest,
        scope: str,
        decision: str,
        reason: str,
        request_digest: str,
        created_at: str,
        *,
        principal_id: str | None = None,
    ) -> None:
        connection.execute(
            """INSERT INTO execution_attempts
               (attempt_id, idempotency_key, actor_role, principal_id, worker_run_id,
                action_id, action_scope, approval_id, experiment_id, offer_id,
                channel_id, decision, reason, request_digest,
                transaction_value_usd, direct_spend_usd, founder_attention_minutes,
                delivery_labor_hours, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                attempt_id,
                idempotency_key,
                _safe_text(request.actor_role, fallback="unknown"),
                _safe_text(principal_id, fallback="unknown", limit=256),
                _safe_text(request.worker_run_id, fallback="") or None,
                _safe_text(request.action_id, fallback="invalid-action"),
                scope,
                _safe_text(request.approval_id, fallback="") or None,
                _safe_text(request.experiment_id, fallback="") or None,
                _safe_text(request.offer_id, fallback="") or None,
                _safe_text(request.channel_id, fallback="") or None,
                decision,
                reason,
                request_digest,
                _amount_text(request.transaction_value_usd),
                _amount_text(request.direct_spend_usd),
                _amount_text(request.founder_attention_minutes),
                _amount_text(request.delivery_labor_hours),
                created_at,
            ),
        )

    def _record_denial(
        self,
        connection: sqlite3.Connection,
        attempt_id: str,
        idempotency_key: str,
        request: ExecutionRequest,
        scope: str,
        request_digest: str,
        created_at: str,
        reason: str,
        *,
        trusted_principal: TrustedPrincipal | None = None,
    ) -> ExecutionOutcome:
        self._insert_attempt(
            connection,
            attempt_id,
            idempotency_key,
            request,
            scope,
            "deny",
            reason,
            request_digest,
            created_at,
            principal_id=(
                trusted_principal.principal_id if trusted_principal is not None else None
            ),
        )
        return ExecutionOutcome(False, "denied", reason, attempt_id)

    @staticmethod
    def _existing_outcome(
        connection: sqlite3.Connection, attempt: sqlite3.Row
    ) -> ExecutionOutcome:
        if attempt["decision"] == "deny":
            return ExecutionOutcome(False, "denied", attempt["reason"], attempt["attempt_id"])
        row = connection.execute(
            "SELECT status, result_json FROM execution_results WHERE attempt_id = ?",
            (attempt["attempt_id"],),
        ).fetchone()
        if row is None:
            return ExecutionOutcome(
                True, "pending", "previous_attempt_pending", attempt["attempt_id"]
            )
        if row["status"] != "verified":
            return ExecutionOutcome(
                True, row["status"], "previous_attempt_not_verified", attempt["attempt_id"]
            )
        try:
            data = json.loads(row["result_json"])
            if not isinstance(data, dict):
                raise TypeError("stored result must be an object")
            expected_reference = _gateway_result_reference(attempt["attempt_id"])
            result = ToolResult(
                action_id=data["action_id"],
                approval_id=data.get("approval_id"),
                external_ref=data["external_ref"],
                verified=data["verified"],
                simulated=data["simulated"],
            )
            if (
                type(result.action_id) is not str
                or result.action_id != attempt["action_id"]
                or type(result.approval_id) not in (str, type(None))
                or result.approval_id != attempt["approval_id"]
                or result.verified is not True
                or result.external_ref != expected_reference
                or type(result.simulated) is not bool
                or (attempt["action_scope"] == "external" and result.simulated is not True)
            ):
                raise ValueError("stored result does not match its execution attempt")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return ExecutionOutcome(
                True,
                "verification_failed",
                "stored_result_invalid",
                attempt["attempt_id"],
            )
        return ExecutionOutcome(True, "verified", "idempotent_replay", attempt["attempt_id"], result)

    def _invoke_tool(
        self,
        binding: ToolBinding,
        request: ExecutionRequest,
        attempt_id: str,
    ) -> ExecutionOutcome:
        handler = binding.handler
        if not callable(handler):
            persisted = self._save_result_safely(
                attempt_id,
                request,
                "tool_error",
                {"error_code": "tool_binding_unavailable"},
            )
            if not persisted:
                return ExecutionOutcome(
                    True, "result_persistence_failed", "result_persistence_failed", attempt_id
                )
            return ExecutionOutcome(True, "tool_error", "tool_binding_unavailable", attempt_id)
        try:
            result = handler(request)
        except Exception:  # noqa: BLE001 - tool failures must not escape as success.
            persisted = self._save_result_safely(
                attempt_id,
                request,
                "tool_error",
                {"error_code": "tool_execution_error"},
            )
            if not persisted:
                return ExecutionOutcome(
                    True, "result_persistence_failed", "result_persistence_failed", attempt_id
                )
            return ExecutionOutcome(True, "tool_error", "tool_execution_error", attempt_id)

        valid = (
            type(result) is ToolResult
            and type(result.action_id) is str
            and result.action_id == request.action_id
            and type(result.approval_id) in (str, type(None))
            and result.approval_id == request.approval_id
            and result.verified is True
            and _valid_result_reference_format(result.external_ref)
            and type(result.simulated) is bool
            and (binding.scope != "external" or result.simulated is True)
        )
        if not valid:
            is_tool_result = type(result) is ToolResult
            safe_result = {
                "error_code": "tool_result_verification_failed",
                "action_id_matches": is_tool_result
                and type(result.action_id) is str
                and result.action_id == request.action_id,
                "approval_id_matches": is_tool_result
                and type(result.approval_id) in (str, type(None))
                and result.approval_id == request.approval_id,
                "external_ref_format_valid": _valid_result_reference_format(
                    result.external_ref
                )
                if is_tool_result
                else False,
                "verified": result.verified is True if is_tool_result else False,
                "simulated": result.simulated is True if is_tool_result else False,
            }
            persisted = self._save_result_safely(
                attempt_id, request, "verification_failed", safe_result
            )
            if not persisted:
                return ExecutionOutcome(
                    True, "result_persistence_failed", "result_persistence_failed", attempt_id
                )
            return ExecutionOutcome(
                True, "verification_failed", "tool_result_verification_failed", attempt_id
            )

        result_reference = _gateway_result_reference(attempt_id)
        safe_result = {
            "action_id": request.action_id,
            "approval_id": request.approval_id,
            "external_ref": result_reference,
            "verified": True,
            "simulated": result.simulated,
        }
        if not self._save_result_safely(attempt_id, request, "verified", safe_result):
            return ExecutionOutcome(
                True, "result_persistence_failed", "result_persistence_failed", attempt_id
            )
        safe_tool_result = ToolResult(
            action_id=request.action_id,
            approval_id=request.approval_id,
            external_ref=result_reference,
            verified=True,
            simulated=result.simulated,
        )
        return ExecutionOutcome(
            True, "verified", "result_verified", attempt_id, safe_tool_result
        )

    def _save_result(self, attempt_id: str, status: str, result: dict[str, object]) -> None:
        result_json = _canonical_json(result)
        with self.store.transaction(immediate=True) as connection:
            connection.execute(
                """INSERT INTO execution_results
                   (result_id, attempt_id, status, result_json, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    uuid.uuid4().hex,
                    attempt_id,
                    status,
                    result_json,
                    _utc_iso(datetime.now(UTC)),
                ),
            )

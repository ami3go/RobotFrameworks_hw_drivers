"""RFDS-008 live evidence engine for rf_votsch_climate_chamber.

This is a different, complementary layer to two things that already exist in
this driver:

- ``diagnostics.py`` (``Get Diagnostics`` / ``Export Diagnostics``) is a
  **point-in-time snapshot** of current session state — one JSON file per
  call. It answers "what is the state right now".
- ``transports/tracing.py`` (``TraceObserver``/``TraceRecord``) already
  captures every outbound/inbound protocol-boundary event per transport, fed
  into ``ClimateChamberCore.diagnostics()['protocol_trace']`` — an in-memory,
  per-session list.

This module answers a different question: "what happened, in what order,
correlated across nested keyword calls, with integrity proof, across the
whole session" — an always-on, append-only, on-disk evidence *run* per
session, written to ``results/session/rf_votsch_climate_chamber/<run>/`` as
JSONL event/operation/error streams plus a SHA-256-hashed manifest. It
reuses the existing ``TraceObserver`` mechanism (via
:meth:`EvidenceRun.attach_to_transport`) rather than re-instrumenting the
transport layer — every ``TraceRecord`` already emitted by
``transports/base.py`` is forwarded here and turned into a
``rfds.protocol_exchange`` JSONL record.

Scope note: this implements the parts of RFDS-008 that make a concrete
troubleshooting difference for this driver (correlated operation/error
records, protocol traces, an integrity-checked manifest, redaction) — it
does not implement platform-scale concerns such as log rotation/backpressure
policy, cryptographic signing, or retention/archival automation. No shared
cross-driver evidence package exists in this repository, so this module is
self-contained rather than importing one, mirroring the equivalent module
built for ``rf_phidget_relay``, ``rf_ea_ps9000t``, and other drivers in this
repository — the schemas and JSONL layout are intentionally identical across
drivers; only the protocol-tracing source differs.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import logging
import os
import platform
import socket
import sys
import threading
import time
import traceback
import uuid
import zipfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .transports.tracing import TraceRecord

SCHEMA_VERSION = "1.0.0"

logger = logging.getLogger("rf_votsch_climate_chamber.evidence")

_SENSITIVE_KEY_MARKERS = ("password", "secret", "token", "api_key", "apikey", "credential", "auth")

_current_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rf_votsch_correlation_id", default=None
)
_current_operation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rf_votsch_operation_id", default=None
)
_current_suite_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rf_votsch_suite_id", default=None
)
_current_test_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rf_votsch_test_id", default=None
)
_current_keyword: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rf_votsch_keyword", default=None
)


def _utc_now_iso() -> str:
    now = datetime.now(UTC)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _new_run_id() -> str:
    now = datetime.now(UTC)
    return (
        f"run-{now.strftime('%Y%m%dT%H%M%S')}.{now.microsecond // 1000:03d}Z-{uuid.uuid4().hex[:8]}"
    )


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    return repr(obj)


def _looks_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in _SENSITIVE_KEY_MARKERS)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


def redact_mapping(data: Mapping[str, Any]) -> dict:
    """Redact keys that look sensitive; recurse into nested mappings (RFDS-008 §29.3)."""
    result: dict = {}
    for key, value in data.items():
        if _looks_sensitive(str(key)):
            result[key] = {"value": "<REDACTED>", "redacted": True, "reason": "credential"}
        else:
            result[key] = _json_safe(value)
    return result


# This driver's own exception hierarchy (rf_votsch_climate_chamber/exceptions.py)
# is already close to an RFDS-007 taxonomy — map to it directly by isinstance
# check against the real base classes, ordered most-specific-base-first, rather
# than by substring-matching the exception's own class name (which misses
# subclasses whose name doesn't happen to contain their category base's name,
# e.g. DriverLimitViolationError(DriverSafetyError) doesn't contain "Safety").
def _classify_exception(exc: BaseException) -> str:
    try:
        from . import exceptions as _exc
    except Exception:
        return "UNKNOWN"
    ordered = (
        (_exc.DriverSafetyError, "SAFETY"),
        (_exc.DriverValidationError, "VALIDATION"),
        (_exc.DriverConnectionError, "CONNECTION"),
        (_exc.DriverTransportError, "TRANSPORT"),
        (_exc.DriverProtocolError, "PROTOCOL"),
        (_exc.DriverDeviceError, "DEVICE"),
        (_exc.DriverResourceError, "RESOURCE"),
        (_exc.DriverDependencyError, "ENVIRONMENT"),
        (_exc.DriverInternalError, "INTERNAL"),
        (_exc.DriverCancelledError, "CANCELLED"),
        (_exc.DriverCleanupError, "CLEANUP"),
        (_exc.DriverStateError, "STATE"),
        (_exc.DriverConfigurationError, "VALIDATION"),
    )
    for exc_type, category in ordered:
        if isinstance(exc, exc_type):
            return category
    return "UNKNOWN"


def _safe_distribution_version(dist_name: str) -> str | None:
    try:
        import importlib.metadata as importlib_metadata

        return importlib_metadata.version(dist_name)
    except Exception:
        return None


def _safe_module_version(module_name: str) -> str | None:
    try:
        module = __import__(module_name)
        return getattr(module, "__version__", None)
    except Exception:
        return None


def _sanitized_hostname() -> str:
    try:
        return hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()[:12]
    except Exception:
        return "UNKNOWN"


class _OperationContext:
    def __init__(self) -> None:
        self.result: Any = None

    def set_result(self, value: Any) -> None:
        self.result = value


class _NullOperationContext:
    def set_result(self, value: Any) -> None:  # pragma: no cover - trivial
        pass


class EvidenceRun:
    """Owns one RFDS-008 result directory for one library instance's session."""

    SCHEMA = "rfds.run_summary"

    def __init__(
        self,
        *,
        driver_id: str = "rf_votsch_climate_chamber",
        activity: str = "session",
        result_root: Path | None = None,
        execution_mode: str = "REAL_HARDWARE",
    ) -> None:
        self.run_id = _new_run_id()
        self.driver_id = driver_id
        self.activity = activity
        self.execution_mode = execution_mode
        base = result_root or Path(os.environ.get("RFDS_EVIDENCE_ROOT", "results"))
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.root = base / activity / driver_id / f"{timestamp}_{self.run_id}"
        self._lock = threading.Lock()
        self._sequence: dict[str, int] = {}
        self._operation_counter = 0
        self._error_counter = 0
        self._start_monotonic = time.monotonic()
        self._start_time = _utc_now_iso()
        self._error_count = 0
        self._warning_count = 0
        self._finalized = False
        self._device_identity: dict = {}
        self._saw_simulator = False
        self._saw_real_hardware = False
        self._make_dirs()
        self._write_environment()
        self.emit_event("RUN_STARTED", f"Evidence run started for driver {driver_id}", level="INFO")

    def _make_dirs(self) -> None:
        for sub in ("events", "protocol", "cleanup", "integrity", "attachments"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def _write_environment(self) -> None:
        payload = {
            "schema": "rfds.environment",
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "timestamp_utc": _utc_now_iso(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "host_token": _sanitized_hostname(),
            "robot_framework_version": _safe_module_version("robot"),
            "driver_distribution_version": _safe_distribution_version("rf-votsch-climate-chamber"),
            "driver_source_version": _safe_module_version("rf_votsch_climate_chamber"),
            "execution_mode": self.execution_mode,
            "clock_synchronization": "UNKNOWN",
        }
        self._write_json(self.root / "environment.json", payload)

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
                encoding="utf-8",
            )

    def _append_jsonl(self, path: Path, stream_key: str, record: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            seq = self._sequence[stream_key] = self._sequence.get(stream_key, 0) + 1
            record = dict(record)
            record["sequence"] = seq
            with path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(record, ensure_ascii=False, sort_keys=True, default=_json_default)
                    + "\n"
                )

    def emit_event(
        self,
        event_type: str,
        message: str,
        *,
        level: str = "INFO",
        data: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
        operation_id: str | None = None,
        session_alias: str | None = None,
    ) -> None:
        record = {
            "schema": "rfds.event",
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "producer_id": f"{self.driver_id}:{session_alias or self.driver_id}",
            "timestamp_utc": _utc_now_iso(),
            "monotonic_ns": time.monotonic_ns(),
            "level": level,
            "event_type": event_type,
            "correlation_id": correlation_id or _current_correlation_id.get(),
            "operation_id": operation_id or _current_operation_id.get(),
            "source": {
                "component": "driver",
                "driver_id": self.driver_id,
                "session_alias": session_alias,
                "suite_id": _current_suite_id.get(),
                "test_id": _current_test_id.get(),
                "robot_keyword": _current_keyword.get(),
            },
            "message": message,
            "data": redact_mapping(dict(data or {})),
        }
        self._append_jsonl(self.root / "events" / "events.jsonl", "events", record)
        python_level = {
            "TRACE": logging.DEBUG,
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }.get(level, logging.INFO)
        logger.log(python_level, "[%s] %s", event_type, message)
        if level == "WARN":
            self._warning_count += 1
        # ERROR/CRITICAL is intentionally not counted here — record_error() below
        # is the sole owner of _error_count to avoid double-counting one failure.

    @contextlib.contextmanager
    def record_operation(
        self,
        capability: str,
        *,
        arguments: Mapping[str, Any] | None = None,
        session_alias: str | None = None,
    ):
        self._operation_counter += 1
        operation_id = f"op-{self._operation_counter:06d}"
        correlation_id = _current_correlation_id.get() or f"corr-{uuid.uuid4().hex[:12]}"
        corr_token = _current_correlation_id.set(correlation_id)
        op_token = _current_operation_id.set(operation_id)
        safe_arguments = redact_mapping(dict(arguments or {}))
        start_monotonic = time.monotonic_ns()
        start_time = _utc_now_iso()
        self.emit_event(
            "OPERATION_STARTED",
            f"{capability} started",
            level="DEBUG",
            correlation_id=correlation_id,
            operation_id=operation_id,
            data={"arguments": safe_arguments},
            session_alias=session_alias,
        )
        ctx = _OperationContext()
        status = "PASS"
        error_summary: str | None = None
        try:
            yield ctx
        except Exception as exc:
            status = "FAIL"
            error_summary = f"{type(exc).__name__}: {exc}"
            self.record_error(
                exc,
                correlation_id=correlation_id,
                operation_id=operation_id,
                capability=capability,
                session_alias=session_alias,
            )
            raise
        finally:
            duration_s = (time.monotonic_ns() - start_monotonic) / 1e9
            record = {
                "schema": "rfds.operation",
                "schema_version": SCHEMA_VERSION,
                "run_id": self.run_id,
                "operation_id": operation_id,
                "correlation_id": correlation_id,
                "capability": capability,
                "session_alias": session_alias,
                "arguments": safe_arguments,
                "start_timestamp_utc": start_time,
                "end_timestamp_utc": _utc_now_iso(),
                "duration_s": round(duration_s, 6),
                "result": _json_safe(ctx.result) if status == "PASS" else None,
                "status": status,
                "error_summary": error_summary,
            }
            self._append_jsonl(self.root / "events" / "operations.jsonl", "operations", record)
            self.emit_event(
                "OPERATION_COMPLETED" if status == "PASS" else "OPERATION_FAILED",
                f"{capability} {'completed' if status == 'PASS' else 'failed'} in {duration_s:.4f}s",
                level="INFO" if status == "PASS" else "ERROR",
                correlation_id=correlation_id,
                operation_id=operation_id,
                session_alias=session_alias,
            )
            _current_correlation_id.reset(corr_token)
            _current_operation_id.reset(op_token)

    def record_trace(self, trace_record: TraceRecord, *, session_alias: str | None = None) -> None:
        """Bridge one ``transports.tracing.TraceRecord`` into protocol evidence.

        Register via :meth:`attach_to_transport` — every write/read/state
        change the transport already reports to its ``TraceObserver`` list
        arrives here automatically, so nothing needs to change in
        ``transports/base.py`` or the SimServ protocol codec.
        """
        # Real event names emitted by transports/{tcp,simulator}.py's BaseTransport._emit:
        # "open", "close", "outbound", "inbound", "state_changed" (from base.py's own
        # _transition). Only "inbound" is a device-to-driver response; everything else
        # (including lifecycle events) is driver-initiated, hence "outbound".
        direction = "inbound" if trace_record.event == "inbound" else "outbound"
        record = {
            "schema": "rfds.protocol_exchange",
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "protocol_exchange_id": f"pex-{uuid.uuid4().hex[:10]}",
            "operation_id": _current_operation_id.get(),
            "correlation_id": _current_correlation_id.get(),
            "timestamp_utc": trace_record.timestamp,
            "transport": trace_record.transport,
            "resource": trace_record.resource,
            "direction": direction,
            "session_alias": session_alias,
            "event": trace_record.event,
            "data_hex": trace_record.data_hex,
            "data_text": trace_record.data_text,
            "details": redact_mapping(dict(trace_record.details or {})),
        }
        self._append_jsonl(self.root / "protocol" / "exchanges.jsonl", "protocol_exchanges", record)
        if trace_record.data_text is not None:
            trace_path = self.root / "protocol" / f"{direction}_trace.log"
            with self._lock, trace_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"{trace_record.timestamp} [{trace_record.operation_id}] {trace_record.data_text!r}\n"
                )

    def note_connection(self, resource: str) -> None:
        """Record whether a connection was to the simulator or a real chamber.

        RFDS-008 §6.6 "simulation honesty": this run's final ``execution_mode``
        (computed in :meth:`finalize`) must not silently claim REAL_HARDWARE
        for a session that only ever talked to ``SIM::...``, nor hide that a
        mixed simulator+real session occurred.
        """
        if str(resource).upper().startswith("SIM::"):
            self._saw_simulator = True
        else:
            self._saw_real_hardware = True

    def attach_to_transport(self, transport: Any, *, session_alias: str | None = None) -> None:
        """Register this run as a trace observer on a live ``BaseTransport``."""

        def _observer(trace_record: TraceRecord) -> None:
            self.record_trace(trace_record, session_alias=session_alias)

        transport.add_trace_observer(_observer)

    def record_error(
        self,
        exc: BaseException,
        *,
        correlation_id: str | None = None,
        operation_id: str | None = None,
        capability: str | None = None,
        session_alias: str | None = None,
        recoverable: bool | None = None,
    ) -> None:
        self._error_counter += 1
        error_id = f"err-{self._error_counter:06d}"
        record = {
            "schema": "rfds.error",
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "error_id": error_id,
            "timestamp_utc": _utc_now_iso(),
            "correlation_id": correlation_id or _current_correlation_id.get(),
            "operation_id": operation_id or _current_operation_id.get(),
            "capability": capability,
            "session_alias": session_alias,
            "category": _classify_exception(exc),
            "exception_type": type(exc).__qualname__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "recoverable": recoverable,
        }
        self._append_jsonl(self.root / "events" / "errors.jsonl", "errors", record)
        self._error_count += 1
        logger.error("[%s] %s (%s): %s", error_id, capability or "?", type(exc).__name__, exc)

    @property
    def has_errors(self) -> bool:
        """Whether :meth:`record_error` has fired at least once this run.

        Used by callers (see ``library.py``'s ``_finalize_evidence``) that
        finalize without an explicit pass/fail verdict of their own, so a run
        containing a recorded failure is never reported as a blanket PASS.
        """
        return self._error_count > 0

    def record_device_identity(self, **fields: Any) -> None:
        self._device_identity.update(
            {key: value for key, value in fields.items() if value is not None}
        )
        payload = {
            "schema": "rfds.device_identity",
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "timestamp_utc": _utc_now_iso(),
            **self._device_identity,
        }
        self._write_json(self.root / "device_identity.json", payload)

    def _write_manifest(self) -> None:
        skip_names = {"evidence_manifest.json", "checksums.sha256"}
        entries = []
        for path in sorted(self.root.rglob("*")):
            if path.is_dir() or path.name in skip_names:
                continue
            relative = path.relative_to(self.root)
            data = path.read_bytes()
            entries.append(
                {
                    "path": str(relative).replace(os.sep, "/"),
                    "role": _role_for(relative),
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        manifest = {
            "schema": "rfds.evidence_manifest",
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "generated_timestamp_utc": _utc_now_iso(),
            "artifact_count": len(entries),
            "artifacts": entries,
        }
        self._write_json(self.root / "evidence_manifest.json", manifest)
        checksum_path = self.root / "integrity" / "checksums.sha256"
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            checksum_path.write_text(
                "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in entries),
                encoding="utf-8",
            )

    def finalize(self, status: str = "PASS") -> Path:
        if self._finalized:
            return self.root
        self.emit_event(
            "RUN_FINISHING", f"Evidence run finalizing with status {status}", level="INFO"
        )
        duration_s = time.monotonic() - self._start_monotonic
        if self._saw_simulator and self._saw_real_hardware:
            self.execution_mode = "MIXED"
        elif self._saw_simulator:
            self.execution_mode = "SIMULATOR"
        elif self._saw_real_hardware:
            self.execution_mode = "REAL_HARDWARE"
        else:
            self.execution_mode = "NO_HARDWARE"
        summary = {
            "schema": self.SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "activity": self.activity,
            "driver_id": self.driver_id,
            "start_timestamp_utc": self._start_time,
            "end_timestamp_utc": _utc_now_iso(),
            "duration_s": round(duration_s, 3),
            "execution_mode": self.execution_mode,
            "final_status": status,
            "error_count": self._error_count,
            "warning_count": self._warning_count,
            "dropped_events": 0,
            "evidence_completeness": "COMPLETE",
            "device_identity_reference": "device_identity.json" if self._device_identity else None,
            "result_root": str(self.root),
        }
        self._write_json(self.root / "run_summary.json", summary)
        self._write_markdown_summary(summary)
        self._write_manifest()
        self._finalized = True
        return self.root

    def _write_markdown_summary(self, summary: dict) -> None:
        lines = [
            f"# Evidence run summary — {summary['driver_id']}",
            "",
            f"- Run ID: `{summary['run_id']}`",
            f"- Activity: {summary['activity']}",
            f"- Execution mode: {summary['execution_mode']}",
            f"- Started: {summary['start_timestamp_utc']}",
            f"- Finished: {summary['end_timestamp_utc']}",
            f"- Duration: {summary['duration_s']} s",
            f"- Final status: **{summary['final_status']}**",
            f"- Errors: {summary['error_count']}, Warnings: {summary['warning_count']}",
            f"- Evidence completeness: {summary['evidence_completeness']}",
            "",
            "Generated from `run_summary.json`. See `events/operations.jsonl` for every keyword",
            "call this run made, `events/errors.jsonl` for failures, and `protocol/exchanges.jsonl`",
            "for the underlying SimServ protocol frames, in the order they happened. For a",
            "point-in-time snapshot instead of this append-only run, see `Get Diagnostics`/",
            "`Export Diagnostics`.",
            "",
        ]
        (self.root / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")

    def export_diagnostic_bundle(self, destination: str | None = None) -> str:
        self._write_manifest()
        if destination:
            zip_path = Path(destination)
            zip_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            zip_path = self.root.parent / f"{self.root.name}_diagnostic_bundle.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(self.root.rglob("*")):
                if path.is_file():
                    archive.write(
                        path, arcname=str(Path(self.root.name) / path.relative_to(self.root))
                    )
        self.emit_event(
            "DIAGNOSTIC_BUNDLE_EXPORTED", f"Diagnostic bundle written to {zip_path}", level="INFO"
        )
        return str(zip_path)


_ROLE_BY_NAME = {
    "run_summary.json": "AUTHORITATIVE_RESULT",
    "run_summary.md": "DERIVED_REPORT",
    "environment.json": "IDENTITY",
    "device_identity.json": "IDENTITY",
}


def _role_for(relative_path: Path) -> str:
    name = relative_path.name
    if name in _ROLE_BY_NAME:
        return _ROLE_BY_NAME[name]
    parts = relative_path.parts
    if parts and parts[0] == "protocol":
        return "RAW_OBSERVATION"
    if relative_path.suffix == ".jsonl":
        return "STRUCTURED_EVENT"
    if parts and parts[0] == "integrity":
        return "INTEGRITY"
    return "DERIVED_REPORT"


class NullEvidenceRun:
    """Used when evidence is disabled: same interface, writes nothing to disk."""

    run_id: str | None = None
    has_errors: bool = False

    @contextlib.contextmanager
    def record_operation(self, capability: str, *, arguments=None, session_alias=None):
        logger.debug("%s(%s)", capability, dict(arguments or {}))
        yield _NullOperationContext()

    def emit_event(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def record_trace(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def note_connection(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def attach_to_transport(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def record_error(self, exc: BaseException, **_kwargs: Any) -> None:
        logger.error("%s: %s", type(exc).__name__, exc)

    def record_device_identity(self, **_kwargs: Any) -> None:
        pass

    def finalize(self, status: str = "PASS") -> None:
        return None

    def export_diagnostic_bundle(self, destination: str | None = None) -> None:
        logger.warning(
            "Diagnostic bundle requested but evidence is disabled; nothing was recorded."
        )
        return None


class EvidenceListener:
    """Optional Robot listener: ``--listener rf_votsch_climate_chamber.evidence.EvidenceListener``."""

    ROBOT_LISTENER_API_VERSION = 3

    def start_suite(self, data: Any, result: Any) -> None:
        _current_suite_id.set(getattr(data, "longname", str(data)))

    def end_suite(self, data: Any, result: Any) -> None:
        _current_suite_id.set(None)

    def start_test(self, data: Any, result: Any) -> None:
        _current_test_id.set(getattr(data, "longname", str(data)))

    def end_test(self, data: Any, result: Any) -> None:
        _current_test_id.set(None)

    def start_keyword(self, data: Any, result: Any) -> None:
        _current_keyword.set(getattr(data, "name", str(data)))

    def end_keyword(self, data: Any, result: Any) -> None:
        _current_keyword.set(None)


__all__ = [
    "SCHEMA_VERSION",
    "EvidenceRun",
    "NullEvidenceRun",
    "EvidenceListener",
    "redact_mapping",
]

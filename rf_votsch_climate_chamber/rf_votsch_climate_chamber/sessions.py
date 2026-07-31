"""Named-session registry and deterministic connection ownership."""

from __future__ import annotations

import datetime as dt
import threading
from dataclasses import dataclass
from urllib.parse import urlparse

from .converters import normalize_alias, to_bool, to_float, to_int
from .core import ClimateChamberCore
from .exceptions import DriverResourceNotFoundError, DriverStateError
from .models import ConnectionRecord, SessionState
from .transports.simulator import SimulatorTransport
from .transports.tcp import TcpTransport


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(slots=True)
class SessionHandle:
    record: ConnectionRecord
    core: ClimateChamberCore
    lock: threading.RLock


class SessionRegistry:
    """Own all chamber sessions for one suite-scoped Robot library instance."""

    def __init__(self, *, default_timeout_s: float = 5.0, default_resource: str | None = None) -> None:
        self.default_timeout_s = float(default_timeout_s)
        self.default_resource = default_resource
        self._sessions: dict[str, SessionHandle] = {}
        self._active_alias: str | None = None
        self._lock = threading.RLock()
        self._generation = 0

    @property
    def active_alias(self) -> str | None:
        with self._lock:
            return self._active_alias

    def select(self, alias: str) -> dict:
        normalized = normalize_alias(alias)
        with self._lock:
            if normalized not in self._sessions:
                raise DriverStateError(
                    f"connection alias {normalized!r} does not exist",
                    operation="Select Connection",
                    recovery_action="connect the alias first",
                )
            self._active_alias = normalized
            return self._sessions[normalized].record.to_robot_dict()

    def resolve_alias(self, alias: str | None) -> str:
        if alias is not None:
            return normalize_alias(alias)
        with self._lock:
            return self._active_alias or "default"

    def get(self, alias: str | None = None, *, require_connected: bool = True) -> SessionHandle:
        normalized = self.resolve_alias(alias)
        with self._lock:
            handle = self._sessions.get(normalized)
        if handle is None:
            raise DriverStateError(
                f"connection alias {normalized!r} is not connected",
                code="RFDS-CON-002",
                operation="resolve session",
                recovery_action="call Connect first",
            )
        if require_connected and not handle.core.is_connected:
            raise DriverStateError(
                f"connection alias {normalized!r} is not connected",
                code="RFDS-CON-002",
                operation="resolve session",
                recovery_action="call Connect or Reconnect",
            )
        return handle

    def connect(
        self,
        resource: str | None,
        *,
        alias: str = "default",
        timeout_s: float | None = None,
        options: dict | None = None,
    ) -> SessionHandle:
        normalized_alias = normalize_alias(alias)
        actual_resource = str(resource or self.default_resource or "").strip()
        if not actual_resource:
            raise DriverResourceNotFoundError(
                "no resource was provided and no default resource is configured",
                operation="Connect",
            )
        settings = dict(options or {})
        effective_timeout = self.default_timeout_s if timeout_s is None else to_float(timeout_s, "timeout_s")
        with self._lock:
            existing = self._sessions.get(normalized_alias)
            if existing is not None:
                if existing.record.resource == actual_resource and existing.core.is_connected:
                    return existing
                raise DriverStateError(
                    f"alias {normalized_alias!r} already owns resource {existing.record.resource!r}",
                    operation="Connect",
                    recovery_action="disconnect the alias or choose another alias",
                )
            self._generation += 1
            record = ConnectionRecord(
                alias=normalized_alias,
                resource=actual_resource,
                state=SessionState.CONNECTING,
                timeout_s=effective_timeout,
                generation=self._generation,
            )

        transport = self._build_transport(actual_resource, effective_timeout, settings)
        is_simulator = actual_resource.upper().startswith("SIM::")
        dryer_output_channel = settings.get("dryer_output_channel")
        compressed_air_output_channel = settings.get("compressed_air_output_channel")
        # The deterministic simulator implements the documented reference mapping.
        # Real chambers remain capability-gated until their physical mapping is
        # explicitly configured by the operator.
        if is_simulator:
            if dryer_output_channel is None:
                dryer_output_channel = 8
            if compressed_air_output_channel is None:
                compressed_air_output_channel = 7
        core = ClimateChamberCore(
            transport,
            temperature_min_c=to_float(settings.get("temperature_min_c", -40.0), "temperature_min_c"),
            temperature_max_c=to_float(settings.get("temperature_max_c", 180.0), "temperature_max_c"),
            timeout_s=effective_timeout,
            response_timeout_s=to_float(settings.get("response_timeout_s", effective_timeout), "response_timeout_s"),
            query_retries=to_int(settings.get("query_retries", 1), "query_retries", minimum=0),
            retry_delay_s=to_float(settings.get("retry_delay_s", 0.25), "retry_delay_s"),
            verify_writes=to_bool(settings.get("verify_writes", True), "verify_writes"),
            setpoint_verify_tolerance_c=to_float(
                settings.get("setpoint_verify_tolerance_c", 0.05), "setpoint_verify_tolerance_c"
            ),
            setpoint_verify_timeout_s=to_float(
                settings.get("setpoint_verify_timeout_s", 15.0), "setpoint_verify_timeout_s"
            ),
            setpoint_verify_poll_interval_s=to_float(
                settings.get("setpoint_verify_poll_interval_s", 0.25),
                "setpoint_verify_poll_interval_s",
            ),
            state_change_timeout_s=to_float(
                settings.get("state_change_timeout_s", 15.0), "state_change_timeout_s"
            ),
            dryer_output_channel=dryer_output_channel,
            compressed_air_output_channel=compressed_air_output_channel,
        )
        handle = SessionHandle(record=record, core=core, lock=threading.RLock())
        try:
            identity = core.connect()
        except Exception as exc:
            record.state = SessionState.ERROR
            record.last_error = exc.to_dict() if hasattr(exc, "to_dict") else {"message": str(exc)}
            core.disconnect()
            raise
        record.state = SessionState.CONNECTED
        record.communication_ok = True
        record.identity = identity
        record.connected_at = utc_now()
        record.last_communication_at = record.connected_at
        with self._lock:
            self._sessions[normalized_alias] = handle
            self._active_alias = normalized_alias
        return handle

    @staticmethod
    def _build_transport(resource: str, timeout_s: float, options: dict):
        if resource.upper().startswith("SIM::"):
            profile = resource.split("::", 1)[1] or "default"
            return SimulatorTransport(profile)
        host: str
        port: int
        if resource.lower().startswith("tcp://"):
            parsed = urlparse(resource)
            if not parsed.hostname:
                raise DriverResourceNotFoundError("TCP resource has no host", operation="Connect")
            host = parsed.hostname
            port = parsed.port or int(options.get("port", 2049))
        elif resource.count(":") == 1:
            host, port_text = resource.rsplit(":", 1)
            port = int(port_text)
        else:
            host = resource
            port = int(options.get("port", 2049))
        return TcpTransport(
            host,
            port,
            timeout_s=timeout_s,
            keepalive=to_bool(options.get("tcp_keepalive", True), "tcp_keepalive"),
        )

    def disconnect(self, alias: str | None, *, safe_shutdown: bool = True, timeout_s: float | None = None) -> None:
        normalized = self.resolve_alias(alias)
        with self._lock:
            handle = self._sessions.get(normalized)
        if handle is None:
            return
        errors: list[Exception] = []
        handle.record.state = SessionState.CLOSING
        if safe_shutdown and handle.core.is_connected:
            try:
                handle.core.safe_shutdown(timeout_s=timeout_s)
            except Exception as exc:
                errors.append(exc)
        try:
            handle.core.disconnect()
        except Exception as exc:
            errors.append(exc)
        handle.record.state = SessionState.DISCONNECTED if not errors else SessionState.ERROR
        handle.record.communication_ok = False
        with self._lock:
            self._sessions.pop(normalized, None)
            if self._active_alias == normalized:
                self._active_alias = next(iter(sorted(self._sessions)), None)
        if errors:
            first = errors[0]
            if len(errors) > 1 and hasattr(first, "details"):
                first.details["additional_cleanup_errors"] = [str(item) for item in errors[1:]]
            raise first

    def disconnect_all(self, *, safe_shutdown: bool = True, timeout_s: float | None = None) -> None:
        with self._lock:
            aliases = list(self._sessions)
        errors: list[str] = []
        for alias in aliases:
            try:
                self.disconnect(alias, safe_shutdown=safe_shutdown, timeout_s=timeout_s)
            except Exception as exc:
                errors.append(f"{alias}: {exc}")
        if errors:
            raise DriverStateError(
                "one or more sessions failed to disconnect cleanly",
                operation="Disconnect All",
                details={"errors": errors},
            )

    def list_states(self) -> list[dict]:
        with self._lock:
            return [self._sessions[key].record.to_robot_dict() for key in sorted(self._sessions)]

    def state_for(self, alias: str | None) -> dict:
        normalized = self.resolve_alias(alias)
        with self._lock:
            handle = self._sessions.get(normalized)
        if handle is None:
            return ConnectionRecord(alias=normalized, resource="", state=SessionState.DISCONNECTED).to_robot_dict()
        return handle.record.to_robot_dict()

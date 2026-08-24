"""D0 compatibility implementation of BaseInstrumentLibrary.

RFDS-003 v2.0 requires the shared ``rfds-core`` distribution.  The project
repository currently does not contain that shared distribution.  This D0 gate
therefore provides a deliberately small compatibility base so device-domain
work and simulator tests can proceed.  It is recorded as DEV-RFDSCORE-001 and
must be replaced by the approved ``rfds-core`` implementation before D1.
"""
from __future__ import annotations

from threading import RLock
from typing import Any, Callable

from ._robot_compat import keyword
from .converters import as_alias, as_resource, as_timeout
from .exceptions import DriverConnectionError, DriverStateError, DriverValidationError
from .models import DriverSession


class BaseInstrumentLibrary:
    def __init__(
        self,
        *,
        metadata: dict[str, Any],
        capabilities: list[str] | tuple[str, ...],
        default_timeout_s: float = 5.0,
        default_resource: str | None = None,
    ) -> None:
        self._metadata = dict(metadata)
        self._capabilities = tuple(sorted(capabilities))
        self._default_timeout_s = as_timeout(default_timeout_s, name="default_timeout_s")
        self._default_resource = as_resource(default_resource)
        self._sessions: dict[str, DriverSession] = {}
        self._active_alias: str | None = None
        self._manager_lock = RLock()

    def _build_transport(self, resource: str, timeout_s: float, options: dict[str, Any]):
        raise NotImplementedError

    def _probe_communication(self, session: DriverSession, timeout_s: float) -> None:
        raise NotImplementedError

    def _read_identity(self, session: DriverSession, timeout_s: float):
        raise NotImplementedError

    def _on_connected(self, session: DriverSession, timeout_s: float) -> None:
        return None

    def _on_disconnecting(self, session: DriverSession, timeout_s: float) -> None:
        return None

    def _resolve_alias(self, alias: object | None, *, require: bool = True) -> str | None:
        normalized = as_alias(alias)
        if normalized is not None:
            return normalized
        if self._active_alias is not None:
            return self._active_alias
        if require:
            raise DriverStateError("no active connection")
        return None

    def _session(self, alias: object | None = None) -> DriverSession:
        name = self._resolve_alias(alias)
        assert name is not None
        session = self._sessions.get(name)
        if session is None or not session.connected:
            raise DriverStateError(f"connection alias {name!r} is not connected", alias=name)
        return session

    def _unknown_state(self, alias: str) -> dict[str, Any]:
        return {
            "alias": alias,
            "resource": None,
            "connected": False,
            "communication_ok": False,
            "transport": None,
            "identity": None,
            "timeout_s": float(self._default_timeout_s),
            "state": "disconnected",
            "simulated": False,
        }

    def _effective_timeout(self, session: DriverSession | None, timeout_s: object | None) -> float:
        if timeout_s is not None:
            return as_timeout(timeout_s)
        if session is not None:
            return float(session.timeout_s)
        return float(self._default_timeout_s)

    def _execute_operation(self, operation: str, call: Callable[[DriverSession, float], Any], *, alias=None, timeout_s=None):
        session = self._session(alias)
        effective = self._effective_timeout(session, timeout_s)
        acquired = session.lock.acquire(timeout=min(effective, 5.0))
        if not acquired:
            from .exceptions import DriverConcurrencyError
            raise DriverConcurrencyError(f"session {session.alias!r} is busy", operation=operation, alias=session.alias)
        try:
            return call(session, effective)
        finally:
            session.lock.release()

    @keyword("Connect", tags=["rfds:connection", "rfds:low_risk"])
    def connect(self, resource=None, alias="default", timeout_s=None, **options) -> dict:
        alias_name = as_alias(alias, default="default")
        assert alias_name is not None
        selected_resource = as_resource(resource) or self._default_resource
        if selected_resource is None:
            raise DriverValidationError("resource is required; use SIM::34972A for simulation")
        effective_timeout = self._effective_timeout(None, timeout_s)
        with self._manager_lock:
            existing = self._sessions.get(alias_name)
            if existing and existing.connected:
                if existing.resource != selected_resource:
                    raise DriverStateError(
                        f"alias {alias_name!r} is already connected to a different resource",
                        alias=alias_name,
                    )
                return existing.state_dict()
            transport = self._build_transport(selected_resource, effective_timeout, dict(options))
            session = DriverSession(
                alias=alias_name,
                resource=selected_resource,
                transport=transport,
                timeout_s=effective_timeout,
                simulated=selected_resource.upper().startswith("SIM::"),
                transport_kind=getattr(getattr(transport, "descriptor", None), "kind", "unknown"),
            )
            try:
                descriptor = transport.open()
                session.transport_kind = descriptor.kind
                self._probe_communication(session, effective_timeout)
                session.identity = self._read_identity(session, effective_timeout)
                self._on_connected(session, effective_timeout)
                session.connected = True
                session.communication_ok = True
                session.state = "connected"
                self._sessions[alias_name] = session
                if self._active_alias is None:
                    self._active_alias = alias_name
                return session.state_dict()
            except Exception as exc:
                session.state = "error"
                try:
                    transport.close(timeout_s=min(effective_timeout, 5.0))
                except Exception:
                    pass
                if isinstance(exc, Exception) and exc.__class__.__module__.startswith("rf_keysight349xx"):
                    raise
                raise DriverConnectionError(
                    f"failed to connect to {selected_resource!r}", operation="Connect", alias=alias_name
                ) from exc

    @keyword("Disconnect", tags=["rfds:connection", "rfds:low_risk"])
    def disconnect(self, alias=None) -> None:
        alias_name = self._resolve_alias(alias, require=False)
        if alias_name is None:
            return
        with self._manager_lock:
            session = self._sessions.get(alias_name)
            if session is None or not session.connected:
                return
            try:
                self._on_disconnecting(session, min(session.timeout_s, 5.0))
            finally:
                try:
                    session.transport.close(timeout_s=min(session.timeout_s, 5.0))
                finally:
                    session.connected = False
                    session.communication_ok = False
                    session.state = "disconnected"
                    if self._active_alias == alias_name:
                        remaining = [name for name, item in self._sessions.items() if item.connected]
                        self._active_alias = sorted(remaining)[0] if remaining else None

    @keyword("Is Connected", tags=["rfds:query", "rfds:low_risk"])
    def is_connected(self, alias=None) -> bool:
        alias_name = self._resolve_alias(alias, require=False)
        if alias_name is None:
            return False
        session = self._sessions.get(alias_name)
        return bool(session and session.connected)

    @keyword("Get Connection State", tags=["rfds:query", "rfds:low_risk"])
    def get_connection_state(self, alias=None, refresh=False) -> dict:
        alias_name = as_alias(alias) or self._active_alias or "default"
        session = self._sessions.get(alias_name)
        if session is None or not session.connected:
            return self._unknown_state(alias_name)
        if str(refresh).strip().lower() in {"1", "true", "yes", "on"}:
            try:
                self._probe_communication(session, session.timeout_s)
            except Exception:
                session.communication_ok = False
                session.state = "faulted"
                raise
            else:
                session.communication_ok = True
                session.state = "connected"
        return session.state_dict()

    @keyword("Check Communication", tags=["rfds:query", "rfds:low_risk"])
    def check_communication(self, alias=None) -> bool:
        session = self._session(alias)
        try:
            self._probe_communication(session, session.timeout_s)
        except Exception:
            session.communication_ok = False
            session.state = "faulted"
            raise
        session.communication_ok = True
        session.state = "connected"
        return True

    @keyword("Get Identity", tags=["rfds:identity", "rfds:low_risk"])
    def get_identity(self, alias=None, refresh=False) -> str:
        session = self._session(alias)
        if str(refresh).strip().lower() in {"1", "true", "yes", "on"}:
            session.identity = self._read_identity(session, session.timeout_s)
        if session.identity is None:
            raise DriverStateError("identity is not available", alias=session.alias)
        return session.identity.display()

    @keyword("Get Driver Information", tags=["rfds:metadata", "rfds:low_risk"])
    def get_driver_information(self) -> dict:
        result = dict(self._metadata)
        result["capability_ids"] = list(self._capabilities)
        return result

    @keyword("Get Driver Capabilities", tags=["rfds:metadata", "rfds:low_risk"])
    def get_driver_capabilities(self) -> list[str]:
        return list(self._capabilities)

    @keyword("Set Communication Timeout", tags=["rfds:configuration", "rfds:low_risk"])
    def set_communication_timeout(self, timeout_s, alias=None) -> float:
        value = as_timeout(timeout_s)
        alias_name = self._resolve_alias(alias, require=False)
        if alias_name is None:
            self._default_timeout_s = value
            return value
        session = self._sessions.get(alias_name)
        if session is None or not session.connected:
            raise DriverStateError(f"connection alias {alias_name!r} is not connected", alias=alias_name)
        session.timeout_s = value
        return value

    @keyword("Get Communication Timeout", tags=["rfds:configuration", "rfds:low_risk"])
    def get_communication_timeout(self, alias=None) -> float:
        alias_name = self._resolve_alias(alias, require=False)
        if alias_name is None:
            return float(self._default_timeout_s)
        session = self._sessions.get(alias_name)
        if session is None or not session.connected:
            raise DriverStateError(f"connection alias {alias_name!r} is not connected", alias=alias_name)
        return float(session.timeout_s)

    @keyword("List Connections", tags=["rfds:connection", "rfds:query", "rfds:low_risk"])
    def list_connections(self) -> list[dict]:
        return [self._sessions[name].state_dict() for name in sorted(self._sessions)]

    @keyword("Select Connection", tags=["rfds:connection", "rfds:low_risk"])
    def select_connection(self, alias) -> dict:
        session = self._session(alias)
        self._active_alias = session.alias
        return session.state_dict()

    @keyword("Disconnect All", tags=["rfds:connection", "rfds:low_risk"])
    def disconnect_all(self) -> None:
        for alias_name in list(self._sessions):
            self.disconnect(alias_name)

    @keyword("Get Active Connection", tags=["rfds:connection", "rfds:query", "rfds:low_risk"])
    def get_active_connection(self) -> str | None:
        return self._active_alias

"""Asynchronous facade using one serialized worker around the synchronous driver."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from .config import DriverConfig
from .device import BK8500B
from .diagnostics import AuditSink, MetricsSink
from .exceptions import IndeterminateCommandOutcome
from .measurements import *  # public annotations mirror the synchronous API
from .status import *
from .transport import Transport


class AsyncBK8500B:
    def __init__(
        self,
        config: DriverConfig,
        *,
        transport: Transport | None = None,
        audit_sink: AuditSink | None = None,
        metrics_sink: MetricsSink | None = None,
    ) -> None:
        self._sync = BK8500B(
            config,
            transport=transport,
            audit_sink=audit_sink,
            metrics_sink=metrics_sink,
        )
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bk8500b")
        self._worker_closed = False

    @property
    def connected(self) -> bool:
        return self._sync.connected

    @property
    def session_state(self):
        return self._sync.session_state

    async def _call(self, name: str, *args: Any, state_changing: bool = False, **kwargs: Any) -> Any:
        if self._worker_closed:
            raise RuntimeError("AsyncBK8500B worker is closed")
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(
            self._worker,
            partial(getattr(self._sync, name), *args, **kwargs),
        )
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError as exc:
            # The worker is serialized and cannot be force-stopped safely. Wait for it
            # to release the session lock, then report conservative semantics.
            try:
                await asyncio.shield(future)
            except Exception:
                pass
            if state_changing:
                raise IndeterminateCommandOutcome(
                    f"Async operation {name!r} was cancelled after dispatch; inspect device state"
                ) from exc
            raise

    async def connect(self) -> None:
        await self._call("connect", state_changing=True)

    async def close(self) -> None:
        if self._worker_closed:
            return
        try:
            await self._call("close", state_changing=True)
        finally:
            self._worker.shutdown(wait=True, cancel_futures=False)
            self._worker_closed = True

    async def __aenter__(self) -> "AsyncBK8500B":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def reconnect(self):
        return await self._call("reconnect", state_changing=True)

    async def synchronize_state(self):
        return await self._call("synchronize_state")

    async def health_check(self):
        return await self._call("health_check")

    async def diagnostic_snapshot(self):
        return await self._call("diagnostic_snapshot")

    async def identify(self):
        return await self._call("identify")

    async def get_scpi_version(self):
        return await self._call("get_scpi_version")

    async def get_capabilities(self, *, refresh: bool = False):
        return await self._call("get_capabilities", refresh=refresh)

    async def clear_status(self):
        return await self._call("clear_status", state_changing=True)

    async def set_event_status_enable(self, value: int):
        return await self._call("set_event_status_enable", value, state_changing=True)

    async def get_event_status_enable(self):
        return await self._call("get_event_status_enable")

    async def read_event_status_register(self):
        return await self._call("read_event_status_register")

    async def operation_complete(self, *, timeout_s: float | None = None):
        return await self._call("operation_complete", timeout_s=timeout_s)

    async def is_operation_complete(self, *, timeout_s: float | None = None):
        return await self._call("is_operation_complete", timeout_s=timeout_s)

    async def set_power_on_status_clear(self, enabled: bool):
        return await self._call("set_power_on_status_clear", enabled, state_changing=True)

    async def get_power_on_status_clear(self):
        return await self._call("get_power_on_status_clear")

    async def save_state(self, slot: int):
        return await self._call("save_state", slot, state_changing=True)

    async def recall_state(self, slot: int):
        return await self._call("recall_state", slot, state_changing=True)

    async def reset_device(self):
        return await self._call("reset_device", state_changing=True)

    async def set_service_request_enable(self, value: int):
        return await self._call("set_service_request_enable", value, state_changing=True)

    async def get_service_request_enable(self):
        return await self._call("get_service_request_enable")

    async def read_status_byte(self):
        return await self._call("read_status_byte")

    async def self_test(self, *, timeout_s: float | None = None):
        return await self._call("self_test", timeout_s=timeout_s, state_changing=True)

    async def get_input_enabled(self):
        return await self._call("get_input_enabled")

    async def set_input_enabled(self, enabled: bool, *, token: SafetyToken | None = None):
        return await self._call("set_input_enabled", enabled, token=token, state_changing=True)

    async def get_short_enabled(self):
        return await self._call("get_short_enabled")

    async def set_short_enabled(self, enabled: bool, *, token: SafetyToken):
        return await self._call("set_short_enabled", enabled, token=token, state_changing=True)

    async def get_operating_mode(self):
        return await self._call("get_operating_mode")

    async def set_operating_mode(self, mode):
        return await self._call("set_operating_mode", mode, state_changing=True)

    async def get_current_setpoint(self):
        return await self._call("get_current_setpoint")

    async def set_current_setpoint(self, amperes: float):
        return await self._call("set_current_setpoint", amperes, state_changing=True)

    async def get_voltage_setpoint(self):
        return await self._call("get_voltage_setpoint")

    async def set_voltage_setpoint(self, volts: float):
        return await self._call("set_voltage_setpoint", volts, state_changing=True)

    async def get_power_setpoint(self):
        return await self._call("get_power_setpoint")

    async def set_power_setpoint(self, watts: float):
        return await self._call("set_power_setpoint", watts, state_changing=True)

    async def get_resistance_setpoint(self):
        return await self._call("get_resistance_setpoint")

    async def set_resistance_setpoint(self, ohms: float):
        return await self._call("set_resistance_setpoint", ohms, state_changing=True)

    async def get_current_range(self):
        return await self._call("get_current_range")

    async def set_current_range(self, amperes: float):
        return await self._call("set_current_range", amperes, state_changing=True)

    async def get_voltage_range(self):
        return await self._call("get_voltage_range")

    async def set_voltage_range(self, volts: float):
        return await self._call("set_voltage_range", volts, state_changing=True)

    async def get_voltage_autorange(self):
        return await self._call("get_voltage_autorange")

    async def set_voltage_autorange(self, enabled: bool):
        return await self._call("set_voltage_autorange", enabled, state_changing=True)

    async def get_current_slew(self):
        return await self._call("get_current_slew")

    async def set_current_slew(self, value: float):
        return await self._call("set_current_slew", value, state_changing=True)

    async def set_current_slew_rise(self, value: float):
        return await self._call("set_current_slew_rise", value, state_changing=True)

    async def set_current_slew_fall(self, value: float):
        return await self._call("set_current_slew_fall", value, state_changing=True)

    async def get_remote_sense(self):
        return await self._call("get_remote_sense")

    async def set_remote_sense(self, enabled: bool):
        return await self._call("set_remote_sense", enabled, state_changing=True)

    async def get_load_on_voltage(self):
        return await self._call("get_load_on_voltage")

    async def set_load_on_voltage(self, volts: float):
        return await self._call("set_load_on_voltage", volts, state_changing=True)

    async def get_load_off_voltage(self):
        return await self._call("get_load_off_voltage")

    async def set_load_off_voltage(self, volts: float):
        return await self._call("set_load_off_voltage", volts, state_changing=True)

    async def measure_voltage(self):
        return await self._call("measure_voltage")

    async def measure_voltage_maximum(self):
        return await self._call("measure_voltage_maximum")

    async def measure_voltage_minimum(self):
        return await self._call("measure_voltage_minimum")

    async def measure_voltage_peak_to_peak(self):
        return await self._call("measure_voltage_peak_to_peak")

    async def measure_current(self):
        return await self._call("measure_current")

    async def measure_current_maximum(self):
        return await self._call("measure_current_maximum")

    async def measure_current_minimum(self):
        return await self._call("measure_current_minimum")

    async def measure_current_peak_to_peak(self):
        return await self._call("measure_current_peak_to_peak")

    async def measure_power(self):
        return await self._call("measure_power")

    async def measure_resistance(self):
        return await self._call("measure_resistance")

    async def measure_all(self):
        return await self._call("measure_all")

    async def configure_and_enable(self, config: SafeEnableConfig, *, token: SafetyToken | None = None):
        return await self._call("configure_and_enable", config, token=token, state_changing=True)

    async def configure_transient(self, config: TransientConfig):
        return await self._call("configure_transient", config, state_changing=True)

    async def get_transient_config(self):
        return await self._call("get_transient_config")

    async def configure_led(self, config: LEDConfig):
        return await self._call("configure_led", config, state_changing=True)

    async def get_led_config(self):
        return await self._call("get_led_config")

    async def configure_ocp_test(self, config: OCPTestConfig):
        return await self._call("configure_ocp_test", config, state_changing=True)

    async def run_ocp_test(self, *, timeout_s: float | None = None):
        return await self._call("run_ocp_test", timeout_s=timeout_s, state_changing=True)

    async def configure_timing_test(self, config: TimingTestConfig):
        return await self._call("configure_timing_test", config, state_changing=True)

    async def run_timing_test(self, *, timeout_s: float | None = None):
        return await self._call("run_timing_test", timeout_s=timeout_s, state_changing=True)

    async def configure_list(self, config: ListConfig):
        return await self._call("configure_list", config, state_changing=True)

    async def run_list(self, *, timeout_s: float | None = None):
        return await self._call("run_list", timeout_s=timeout_s, state_changing=True)

    async def trigger(self):
        return await self._call("trigger", state_changing=True)

    async def clear_protection(self, *, token: SafetyToken):
        return await self._call("clear_protection", token=token, state_changing=True)

    async def get_device_status(self):
        return await self._call("get_device_status")

    async def read_questionable_event(self):
        return await self._call("read_questionable_event")

    async def read_questionable_condition(self):
        return await self._call("read_questionable_condition")

    async def set_questionable_enable(self, value: int):
        return await self._call("set_questionable_enable", value, state_changing=True)

    async def get_questionable_enable(self):
        return await self._call("get_questionable_enable")

    async def read_operation_event(self):
        return await self._call("read_operation_event")

    async def read_operation_condition(self):
        return await self._call("read_operation_condition")

    async def set_operation_enable(self, value: int):
        return await self._call("set_operation_enable", value, state_changing=True)

    async def get_operation_enable(self):
        return await self._call("get_operation_enable")

    async def read_next_error(self):
        return await self._call("read_next_error")

    async def drain_error_queue(self, *, maximum: int | None = None):
        return await self._call("drain_error_queue", maximum=maximum)

    async def write_raw_scpi(self, command: str, *, timeout_s: float | None = None):
        return await self._call("write_raw_scpi", command, timeout_s=timeout_s, state_changing=True)

    async def query_raw_scpi(self, command: str, *, timeout_s: float | None = None):
        return await self._call("query_raw_scpi", command, timeout_s=timeout_s, state_changing=True)

    async def transact_raw_legacy(self, frame: bytes, *, timeout_s: float | None = None):
        return await self._call("transact_raw_legacy", frame, timeout_s=timeout_s, state_changing=True)

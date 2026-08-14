"""Backend layer: the real per-series ``picosdk`` SDKs, and the in-process simulator.

Per RFDS-004's intent (the spec itself only names VISA/serial/socket/USB
transports, not an SDK), all ``picosdk`` ctypes calls are confined to this
module — ``driver.py`` never imports ``picosdk`` directly and only talks to
the :class:`PicoScopeBackend` protocol, so it works identically against any
series or :class:`~picoscope_scope.simulator.SimulatedBackend`.

One concrete backend class per SDK series (``RealPs2000aBackend``,
``RealPs3000aBackend``, ...), registered in ``driver.py``'s
``_REAL_BACKEND_BY_SERIES``. Pico's "X000A"-generation API family
(ps2000a, ps3000a, and presumably ps4000a/ps5000a later) shares identical
function signatures and enum values for everything this driver uses
(confirmed against the real ``picosdk`` source for both series currently
implemented) — each backend class below is a near-mechanical prefix swap of
the last, which is why adding another series is expected to be a small,
repetitive addition rather than new design work.

Every backend class's ``picosdk`` calls are written from the documented API
but — no ``pip``/vendor driver/hardware is available in the environment this
was built in — **none of them** have been executed against the real
``picosdk`` package or a physical instrument. Treat every ``RealPsXXXXBackend``
class here as reviewed-not-run until it's exercised on a machine with
``picosdk`` and Pico's native driver installed.
"""

from __future__ import annotations

from typing import Protocol

from .exceptions import (
    PicoScopeConnectionError,
    PicoScopeDeviceError,
    PicoScopeTimeoutError,
)

# Channel index (A=0..D=3) is identical across every supported series'
# PS<nnnn>A_CHANNEL enum, so one shared table covers all of them.
_CHANNEL_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}


class PicoScopeBackend(Protocol):
    """Boundary every backend implements identically; extended as later steps need more."""

    def enumerate_devices(self) -> list[str]: ...

    def open(self, serial: str) -> None: ...

    def close(self) -> None: ...

    def is_open(self) -> bool: ...

    def get_unit_info(self) -> dict[str, str]: ...

    def set_channel(
        self, channel: str, enabled: bool, coupling: int, range_index: int, offset_v: float
    ) -> None: ...

    def maximum_adc_value(self) -> int: ...

    def get_timebase(self, timebase_index: int, num_samples: int) -> tuple[float, int]: ...

    def set_simple_trigger(
        self,
        enabled: bool,
        channel: str,
        threshold_adc: int,
        direction: int,
        delay_samples: int,
        auto_trigger_ms: int,
    ) -> None: ...

    def run_block_capture(
        self,
        pre_samples: int,
        post_samples: int,
        timebase_index: int,
        channels: list[str],
        timeout_s: float,
    ) -> dict[str, list[int]]: ...

    def set_sig_gen_built_in(
        self, offset_uv: int, pk_to_pk_uv: int, wave_type: int, frequency_hz: float
    ) -> None: ...


class RealPs2000aBackend:
    """``picosdk.ps2000a`` ctypes backend.

    Import of ``picosdk`` is deferred to :meth:`open` so this module (and the
    whole package) stays importable without ``picosdk`` installed when only
    the simulator is used — no device I/O happens at import time either way.
    """

    def __init__(self) -> None:
        self._handle = None
        self._ps = None
        self._functions = None
        self._serial: str | None = None

    def _import_sdk(self):
        try:
            from picosdk import ps2000a
            from picosdk import functions as picosdk_functions
        except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
            raise PicoScopeConnectionError(
                "picosdk is not installed; install rf_picoscope_scope[hardware] "
                "(and Pico's native PicoSDK driver package) for real hardware"
            ) from exc
        return ps2000a, picosdk_functions

    def enumerate_devices(self) -> list[str]:
        ps, functions = self._import_sdk()
        import ctypes

        count = ctypes.c_int16(0)
        serials = ctypes.create_string_buffer(256)
        serial_len = ctypes.c_int16(len(serials.raw))
        status = ps.ps2000aEnumerateUnits(ctypes.byref(count), serials, ctypes.byref(serial_len))
        functions.assert_pico_ok(status)
        if count.value == 0:
            return []
        return [s for s in serials.value.decode("ascii").split(",") if s]

    def open(self, serial: str) -> None:
        ps, functions = self._import_sdk()
        import ctypes

        handle = ctypes.c_int16()
        status = ps.ps2000aOpenUnit(ctypes.byref(handle), serial.encode("ascii"))
        try:
            functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeConnectionError(
                f"could not open PicoScope with serial {serial!r}: {exc}"
            ) from exc
        self._ps = ps
        self._functions = functions
        self._handle = handle
        self._serial = serial

    def close(self) -> None:
        if self._handle is not None and self._ps is not None:
            self._ps.ps2000aCloseUnit(self._handle)
        self._handle = None
        self._ps = None
        self._functions = None
        self._serial = None

    def is_open(self) -> bool:
        return self._handle is not None

    def _require_open(self):
        if self._handle is None or self._ps is None:
            raise PicoScopeConnectionError("backend is not open")
        return self._ps, self._handle

    def get_unit_info(self) -> dict[str, str]:
        ps, handle = self._require_open()
        import ctypes

        from picosdk.constants import PICO_INFO

        def _line(info_key: str) -> str:
            buf = ctypes.create_string_buffer(256)
            required = ctypes.c_int16(0)
            status = ps.ps2000aGetUnitInfo(
                handle, buf, ctypes.c_int16(len(buf)), ctypes.byref(required), PICO_INFO[info_key]
            )
            self._functions.assert_pico_ok(status)
            return buf.value.decode("ascii").strip()

        try:
            return {
                "manufacturer": "Pico Technology",
                "model": _line("PICO_VARIANT_INFO"),
                "serial": _line("PICO_BATCH_AND_SERIAL"),
                "firmware": _line("PICO_HARDWARE_VERSION"),
                "driver_version": _line("PICO_DRIVER_VERSION"),
            }
        except Exception as exc:  # picosdk raises its own exception types via assert_pico_ok
            raise PicoScopeDeviceError(f"could not read unit info: {exc}") from exc

    def set_channel(
        self, channel: str, enabled: bool, coupling: int, range_index: int, offset_v: float
    ) -> None:
        ps, handle = self._require_open()
        import ctypes

        status = ps.ps2000aSetChannel(
            handle,
            _CHANNEL_INDEX[channel],
            1 if enabled else 0,
            int(coupling),
            int(range_index),
            ctypes.c_float(offset_v),
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(
                f"ps2000aSetChannel failed for channel {channel!r}: {exc}"
            ) from exc

    def maximum_adc_value(self) -> int:
        ps, handle = self._require_open()
        import ctypes

        max_adc = ctypes.c_int16()
        status = ps.ps2000aMaximumValue(handle, ctypes.byref(max_adc))
        self._functions.assert_pico_ok(status)
        return int(max_adc.value)

    def get_timebase(self, timebase_index: int, num_samples: int) -> tuple[float, int]:
        """Delegates entirely to ``ps2000aGetTimebase2`` — the device is the sole
        authority on which timebase indices are valid and what interval they give,
        so (unlike the simulator) this never guesses at the formula itself."""

        ps, handle = self._require_open()
        import ctypes

        interval_ns = ctypes.c_float()
        max_samples = ctypes.c_int32()
        status = ps.ps2000aGetTimebase2(
            handle,
            ctypes.c_uint32(timebase_index),
            ctypes.c_int32(num_samples),
            ctypes.byref(interval_ns),
            0,
            ctypes.byref(max_samples),
            0,
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(
                f"ps2000aGetTimebase2 failed for timebase {timebase_index}: {exc}"
            ) from exc
        return interval_ns.value * 1e-9, int(max_samples.value)

    def set_simple_trigger(
        self,
        enabled: bool,
        channel: str,
        threshold_adc: int,
        direction: int,
        delay_samples: int,
        auto_trigger_ms: int,
    ) -> None:
        ps, handle = self._require_open()
        import ctypes

        status = ps.ps2000aSetSimpleTrigger(
            handle,
            1 if enabled else 0,
            _CHANNEL_INDEX[channel],
            ctypes.c_int16(threshold_adc),
            int(direction),
            ctypes.c_uint32(delay_samples),
            ctypes.c_int16(auto_trigger_ms),
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps2000aSetSimpleTrigger failed: {exc}") from exc

    def run_block_capture(
        self,
        pre_samples: int,
        post_samples: int,
        timebase_index: int,
        channels: list[str],
        timeout_s: float,
    ) -> dict[str, list[int]]:
        ps, handle = self._require_open()
        import ctypes
        import time

        time_indisposed_ms = ctypes.c_int32()
        status = ps.ps2000aRunBlock(
            handle,
            ctypes.c_int32(pre_samples),
            ctypes.c_int32(post_samples),
            ctypes.c_uint32(timebase_index),
            0,
            ctypes.byref(time_indisposed_ms),
            0,
            None,
            None,
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps2000aRunBlock failed: {exc}") from exc

        ready = ctypes.c_int16(0)
        deadline = time.monotonic() + timeout_s
        while not ready.value:
            status = ps.ps2000aIsReady(handle, ctypes.byref(ready))
            self._functions.assert_pico_ok(status)
            if not ready.value:
                if time.monotonic() > deadline:
                    raise PicoScopeTimeoutError(
                        f"block capture did not become ready within {timeout_s:g} s"
                    )
                time.sleep(0.001)

        total_samples = pre_samples + post_samples
        buffers = {}
        for channel in channels:
            buf = (ctypes.c_int16 * total_samples)()
            status = ps.ps2000aSetDataBuffer(
                handle, _CHANNEL_INDEX[channel], ctypes.byref(buf), total_samples, 0, 0
            )
            self._functions.assert_pico_ok(status)
            buffers[channel] = buf

        n_samples = ctypes.c_int32(total_samples)
        overflow = ctypes.c_int16()
        status = ps.ps2000aGetValues(
            handle, 0, ctypes.byref(n_samples), 0, 0, 0, ctypes.byref(overflow)
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps2000aGetValues failed: {exc}") from exc

        return {channel: list(buffers[channel])[: n_samples.value] for channel in channels}

    def set_sig_gen_built_in(
        self, offset_uv: int, pk_to_pk_uv: int, wave_type: int, frequency_hz: float
    ) -> None:
        """No sweep support (matches this driver's scope): start==stop frequency,
        zero increment/dwell, free-run (shots=0, sweeps=0, no external trigger)."""

        ps, handle = self._require_open()
        import ctypes

        status = ps.ps2000aSetSigGenBuiltIn(
            handle,
            ctypes.c_int32(offset_uv),
            ctypes.c_uint32(pk_to_pk_uv),
            int(wave_type),
            ctypes.c_float(frequency_hz),
            ctypes.c_float(frequency_hz),
            ctypes.c_float(0.0),
            ctypes.c_float(0.0),
            0,  # sweep_type: UP
            0,  # operation: ES_OFF
            0,  # shots
            0,  # sweeps
            0,  # trigger_type: SIGGEN_RISING
            0,  # trigger_source: SIGGEN_NONE
            0,  # ext_in_threshold
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps2000aSetSigGenBuiltIn failed: {exc}") from exc


class RealPs3000aBackend:
    """``picosdk.ps3000a`` ctypes backend.

    Import of ``picosdk`` is deferred to :meth:`open` so this module (and the
    whole package) stays importable without ``picosdk`` installed when only
    the simulator is used — no device I/O happens at import time either way.
    """

    def __init__(self) -> None:
        self._handle = None
        self._ps = None
        self._functions = None
        self._serial: str | None = None

    def _import_sdk(self):
        try:
            from picosdk import ps3000a
            from picosdk import functions as picosdk_functions
        except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
            raise PicoScopeConnectionError(
                "picosdk is not installed; install rf_picoscope_scope[hardware] "
                "(and Pico's native PicoSDK driver package) for real hardware"
            ) from exc
        return ps3000a, picosdk_functions

    def enumerate_devices(self) -> list[str]:
        ps, functions = self._import_sdk()
        import ctypes

        count = ctypes.c_int16(0)
        serials = ctypes.create_string_buffer(256)
        serial_len = ctypes.c_int16(len(serials.raw))
        status = ps.ps3000aEnumerateUnits(ctypes.byref(count), serials, ctypes.byref(serial_len))
        functions.assert_pico_ok(status)
        if count.value == 0:
            return []
        return [s for s in serials.value.decode("ascii").split(",") if s]

    def open(self, serial: str) -> None:
        ps, functions = self._import_sdk()
        import ctypes

        handle = ctypes.c_int16()
        status = ps.ps3000aOpenUnit(ctypes.byref(handle), serial.encode("ascii"))
        try:
            functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeConnectionError(
                f"could not open PicoScope with serial {serial!r}: {exc}"
            ) from exc
        self._ps = ps
        self._functions = functions
        self._handle = handle
        self._serial = serial

    def close(self) -> None:
        if self._handle is not None and self._ps is not None:
            self._ps.ps3000aCloseUnit(self._handle)
        self._handle = None
        self._ps = None
        self._functions = None
        self._serial = None

    def is_open(self) -> bool:
        return self._handle is not None

    def _require_open(self):
        if self._handle is None or self._ps is None:
            raise PicoScopeConnectionError("backend is not open")
        return self._ps, self._handle

    def get_unit_info(self) -> dict[str, str]:
        ps, handle = self._require_open()
        import ctypes

        from picosdk.constants import PICO_INFO

        def _line(info_key: str) -> str:
            buf = ctypes.create_string_buffer(256)
            required = ctypes.c_int16(0)
            status = ps.ps3000aGetUnitInfo(
                handle, buf, ctypes.c_int16(len(buf)), ctypes.byref(required), PICO_INFO[info_key]
            )
            self._functions.assert_pico_ok(status)
            return buf.value.decode("ascii").strip()

        try:
            return {
                "manufacturer": "Pico Technology",
                "model": _line("PICO_VARIANT_INFO"),
                "serial": _line("PICO_BATCH_AND_SERIAL"),
                "firmware": _line("PICO_HARDWARE_VERSION"),
                "driver_version": _line("PICO_DRIVER_VERSION"),
            }
        except Exception as exc:  # picosdk raises its own exception types via assert_pico_ok
            raise PicoScopeDeviceError(f"could not read unit info: {exc}") from exc

    def set_channel(
        self, channel: str, enabled: bool, coupling: int, range_index: int, offset_v: float
    ) -> None:
        ps, handle = self._require_open()
        import ctypes

        status = ps.ps3000aSetChannel(
            handle,
            _CHANNEL_INDEX[channel],
            1 if enabled else 0,
            int(coupling),
            int(range_index),
            ctypes.c_float(offset_v),
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(
                f"ps3000aSetChannel failed for channel {channel!r}: {exc}"
            ) from exc

    def maximum_adc_value(self) -> int:
        ps, handle = self._require_open()
        import ctypes

        max_adc = ctypes.c_int16()
        status = ps.ps3000aMaximumValue(handle, ctypes.byref(max_adc))
        self._functions.assert_pico_ok(status)
        return int(max_adc.value)

    def get_timebase(self, timebase_index: int, num_samples: int) -> tuple[float, int]:
        """Delegates entirely to ``ps3000aGetTimebase2`` — the device is the sole
        authority on which timebase indices are valid and what interval they give,
        so (unlike the simulator) this never guesses at the formula itself."""

        ps, handle = self._require_open()
        import ctypes

        interval_ns = ctypes.c_float()
        max_samples = ctypes.c_int32()
        status = ps.ps3000aGetTimebase2(
            handle,
            ctypes.c_uint32(timebase_index),
            ctypes.c_int32(num_samples),
            ctypes.byref(interval_ns),
            0,
            ctypes.byref(max_samples),
            0,
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(
                f"ps3000aGetTimebase2 failed for timebase {timebase_index}: {exc}"
            ) from exc
        return interval_ns.value * 1e-9, int(max_samples.value)

    def set_simple_trigger(
        self,
        enabled: bool,
        channel: str,
        threshold_adc: int,
        direction: int,
        delay_samples: int,
        auto_trigger_ms: int,
    ) -> None:
        ps, handle = self._require_open()
        import ctypes

        status = ps.ps3000aSetSimpleTrigger(
            handle,
            1 if enabled else 0,
            _CHANNEL_INDEX[channel],
            ctypes.c_int16(threshold_adc),
            int(direction),
            ctypes.c_uint32(delay_samples),
            ctypes.c_int16(auto_trigger_ms),
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps3000aSetSimpleTrigger failed: {exc}") from exc

    def run_block_capture(
        self,
        pre_samples: int,
        post_samples: int,
        timebase_index: int,
        channels: list[str],
        timeout_s: float,
    ) -> dict[str, list[int]]:
        ps, handle = self._require_open()
        import ctypes
        import time

        time_indisposed_ms = ctypes.c_int32()
        status = ps.ps3000aRunBlock(
            handle,
            ctypes.c_int32(pre_samples),
            ctypes.c_int32(post_samples),
            ctypes.c_uint32(timebase_index),
            0,
            ctypes.byref(time_indisposed_ms),
            0,
            None,
            None,
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps3000aRunBlock failed: {exc}") from exc

        ready = ctypes.c_int16(0)
        deadline = time.monotonic() + timeout_s
        while not ready.value:
            status = ps.ps3000aIsReady(handle, ctypes.byref(ready))
            self._functions.assert_pico_ok(status)
            if not ready.value:
                if time.monotonic() > deadline:
                    raise PicoScopeTimeoutError(
                        f"block capture did not become ready within {timeout_s:g} s"
                    )
                time.sleep(0.001)

        total_samples = pre_samples + post_samples
        buffers = {}
        for channel in channels:
            buf = (ctypes.c_int16 * total_samples)()
            status = ps.ps3000aSetDataBuffer(
                handle, _CHANNEL_INDEX[channel], ctypes.byref(buf), total_samples, 0, 0
            )
            self._functions.assert_pico_ok(status)
            buffers[channel] = buf

        n_samples = ctypes.c_int32(total_samples)
        overflow = ctypes.c_int16()
        status = ps.ps3000aGetValues(
            handle, 0, ctypes.byref(n_samples), 0, 0, 0, ctypes.byref(overflow)
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps3000aGetValues failed: {exc}") from exc

        return {channel: list(buffers[channel])[: n_samples.value] for channel in channels}

    def set_sig_gen_built_in(
        self, offset_uv: int, pk_to_pk_uv: int, wave_type: int, frequency_hz: float
    ) -> None:
        """No sweep support (matches this driver's scope): start==stop frequency,
        zero increment/dwell, free-run (shots=0, sweeps=0, no external trigger)."""

        ps, handle = self._require_open()
        import ctypes

        status = ps.ps3000aSetSigGenBuiltIn(
            handle,
            ctypes.c_int32(offset_uv),
            ctypes.c_uint32(pk_to_pk_uv),
            int(wave_type),
            ctypes.c_float(frequency_hz),
            ctypes.c_float(frequency_hz),
            ctypes.c_float(0.0),
            ctypes.c_float(0.0),
            0,  # sweep_type: UP
            0,  # operation: ES_OFF
            0,  # shots
            0,  # sweeps
            0,  # trigger_type: SIGGEN_RISING
            0,  # trigger_source: SIGGEN_NONE
            0,  # ext_in_threshold
        )
        try:
            self._functions.assert_pico_ok(status)
        except Exception as exc:
            raise PicoScopeDeviceError(f"ps3000aSetSigGenBuiltIn failed: {exc}") from exc

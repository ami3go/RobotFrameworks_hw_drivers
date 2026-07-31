"""Unit tests for the BK8500 driver. No hardware required."""

from __future__ import annotations

import pytest

from bk8500_load import protocol as p
from bk8500_load.driver import BK8500Driver
from bk8500_load.enums import LoadFunction, LoadMode, TriggerSource, limits_for
from bk8500_load.exceptions import (
    BK8500CommandError,
    BK8500ConnectionError,
    BK8500ProtocolError,
    BK8500SafetyError,
    BK8500StateError,
    BK8500ValidationError,
    BK8500VerificationError,
)
from bk8500_load.library import BK8500Library
from bk8500_load.transport import SimulatedTransport


@pytest.fixture()
def driver() -> BK8500Driver:
    load = BK8500Driver.simulated(model="8500", apply_stabilization_delays=False)
    load.connect()
    load.set_remote_control(True)
    yield load
    load.disconnect(safe=False)


# ---------------------------------------------------------------- protocol


def test_checksum_matches_manual_example():
    # Manual "set to remote" example: AA 00 20 01 ... checksum 0xCB
    frame = p.build_frame(0, p.Command.SET_REMOTE, bytes([1]))
    assert frame[0] == 0xAA and frame[2] == 0x20 and frame[3] == 0x01
    assert frame[-1] == 0xCB
    assert len(frame) == 26


def test_uploaded_bench_example_packets_match_driver_protocol():
    remote = p.build_frame(0, p.Command.SET_REMOTE, bytes([1]))
    fixed = p.build_frame(0, p.Command.SET_FUNCTION, bytes([0]))
    assert remote.hex(" ").upper() == (
        "AA 00 20 01 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 CB"
    )
    assert fixed.hex(" ").upper() == (
        "AA 00 5D 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 07"
    )
    assert p.command_expects_status(p.Command.SET_REMOTE)
    assert p.command_expects_status(p.Command.SET_FUNCTION)


def test_encode_decode_roundtrip():
    assert p.decode_int(p.encode_int(31200, 4)) == 31200
    assert p.encode_int(16230, 4) == bytes([0x66, 0x3F, 0x00, 0x00])  # manual 16.23 V example
    assert p.encode_int(31200, 4) == bytes([0xE0, 0x79, 0x00, 0x00])  # manual 3.12 A example
    assert p.encode_int(213450, 4) == bytes([0xCA, 0x41, 0x03, 0x00])  # manual 213.45 W example


def test_encode_rejects_overflow():
    with pytest.raises(ValueError):
        p.encode_int(70000, 2)


def test_frame_validation_detects_bad_checksum():
    frame = bytearray(p.build_frame(0, p.Command.SET_REMOTE, bytes([1])))
    frame[-1] ^= 0xFF
    ok, reason = p.frame_is_well_formed(bytes(frame))
    assert not ok and "checksum" in reason


def test_address_out_of_range_rejected():
    with pytest.raises(ValueError):
        p.build_frame(0xFF, p.Command.SET_REMOTE, bytes([1]))


# ------------------------------------------------------------------ driver


def test_connect_reads_identity_and_sets_limits():
    load = BK8500Driver.simulated(model="8502")
    info = load.connect()
    assert info.model == "8502"
    assert load.limits.max_voltage_v == 500.0
    load.disconnect(safe=False)


def test_unknown_model_falls_back_to_conservative_limits():
    limits = limits_for("9999")
    assert limits.model == "UNKNOWN"
    assert limits.max_current_a == 15.0


def test_cc_setpoint_roundtrip(driver):
    driver.set_setpoint(LoadMode.CC, 2.5)
    assert driver.get_setpoint(LoadMode.CC) == pytest.approx(2.5)


def test_setpoint_above_rating_is_rejected_locally(driver):
    with pytest.raises(BK8500ValidationError) as excinfo:
        driver.set_setpoint("CC", 40.0)
    assert "8500" in str(excinfo.value)


def test_mode_string_is_case_insensitive(driver):
    assert driver.set_mode("cv") is LoadMode.CV
    assert driver.get_mode() is LoadMode.CV


def test_invalid_mode_name_lists_valid_values(driver):
    with pytest.raises(BK8500ValidationError) as excinfo:
        driver.set_mode("CX")
    assert "CC, CV, CW, CR" in str(excinfo.value)


def test_input_cannot_be_enabled_without_remote_control():
    load = BK8500Driver.simulated()
    load.connect()
    with pytest.raises(BK8500StateError):
        load.set_input_state(True)
    load.disconnect(safe=False)


def test_short_function_is_refused_by_default(driver):
    with pytest.raises(BK8500SafetyError):
        driver.set_function("SHORT")
    assert driver.set_function_unchecked("SHORT") is LoadFunction.SHORT


def test_cc_measurement_follows_ohms_law(driver):
    # 12 V source, 50 mOhm series resistance, 2 A sink -> 11.9 V, 23.8 W
    driver.apply_load("CC", 2.0, enable_input=True)
    reading = driver.measure()
    assert reading.current_a == pytest.approx(2.0, abs=1e-3)
    assert reading.voltage_v == pytest.approx(11.9, abs=1e-3)
    assert reading.power_w == pytest.approx(23.8, abs=1e-2)
    assert reading.input_on is True
    assert reading.demand_state["constant_current"] is True


def test_cr_mode_draws_expected_current(driver):
    driver.apply_load("CR", 6.0, enable_input=True)
    reading = driver.measure()
    assert reading.current_a == pytest.approx(12.0 / 6.05, abs=1e-3)


def test_protection_fault_is_raised(driver):
    driver.set_max_current(1.0)
    driver.apply_load("CC", 3.0, enable_input=True)
    with pytest.raises(Exception) as excinfo:
        driver.assert_no_protection_faults()
    assert "over_current" in str(excinfo.value)


def test_transient_roundtrip_uses_tenth_millisecond_units(driver):
    driver.set_transient("CC", 1.0, 0.010, 2.0, 0.020, "PULSE")
    settings = driver.get_transient("CC")
    assert settings.level_a == pytest.approx(1.0)
    assert settings.dwell_a_s == pytest.approx(0.010)
    assert settings.level_b == pytest.approx(2.0)
    assert settings.dwell_b_s == pytest.approx(0.020)
    assert settings.operation.name == "PULSE"


def test_transient_dwell_beyond_field_width_is_rejected(driver):
    with pytest.raises(BK8500ValidationError):
        driver.set_transient("CC", 1.0, 10.0, 2.0, 0.1)


def test_list_programming_roundtrip(driver):
    driver.configure_list("CC", [(0.5, 0.1), (1.5, 0.2), (2.5, 0.3)], repeat="REPEAT", name="LIST1")
    assert driver.get_list_step_count() == 3
    step = driver.get_list_step("CC", 2)
    assert step.index == 2
    assert step.level == pytest.approx(1.5)
    assert step.dwell_s == pytest.approx(0.2)
    assert driver.get_list_name() == "LIST1"


def test_list_name_length_is_validated(driver):
    with pytest.raises(BK8500ValidationError):
        driver.set_list_name("ELEVENCHARS")


def test_settings_register_bounds(driver):
    driver.save_settings(25)
    with pytest.raises(BK8500ValidationError):
        driver.save_settings(26)


def test_trigger_requires_bus_source(driver):
    driver.set_trigger_source(TriggerSource.IMMEDIATE)
    with pytest.raises(BK8500CommandError):
        driver.trigger()
    driver.set_trigger_source("BUS")
    driver.trigger()


def test_command_error_reports_instrument_status(driver):
    with pytest.raises(BK8500CommandError) as excinfo:
        driver.set_list_partition(4)  # valid
        driver._write(p.Command.SET_LIST_PARTITION, bytes([3]))  # invalid partition
    assert excinfo.value.status == p.StatusCode.PARAMETER_INCORRECT


def test_operations_without_connection_fail_clearly():
    load = BK8500Driver.simulated()
    with pytest.raises(BK8500ConnectionError):
        load.measure()


def test_malformed_response_is_retried_then_raised(monkeypatch):
    load = BK8500Driver.simulated(retries=2, retry_delay_s=0)
    load.connect()
    calls = {"n": 0}
    original = load.transport.transact

    def corrupt(frame):
        calls["n"] += 1
        response = bytearray(original(frame))
        response[-1] ^= 0xFF
        return bytes(response)

    monkeypatch.setattr(load.transport, "transact", corrupt)
    with pytest.raises(BK8500ProtocolError):
        load.get_mode()
    assert calls["n"] == 3  # one attempt plus two retries


def test_wait_until_stable_returns_when_settled(driver):
    driver.apply_load("CC", 1.0, enable_input=True)
    reading = driver.wait_until_stable(
        "current", tolerance=0.001, window_s=0.05, timeout_s=2.0, interval_s=0.001
    )
    assert reading.current_a == pytest.approx(1.0, abs=1e-3)


def test_wait_until_stable_times_out_when_moving(driver, monkeypatch):
    driver.apply_load("CC", 1.0, enable_input=True)
    sim: SimulatedTransport = driver.transport
    original = driver.measure

    def drifting():
        sim.source_voltage_v += 1.0
        return original()

    monkeypatch.setattr(driver, "measure", drifting)
    with pytest.raises(BK8500StateError):
        driver.wait_until_stable(
            "voltage", tolerance=0.01, window_s=0.05, timeout_s=0.3, interval_s=0.001
        )


def test_safe_state_opens_the_input(driver):
    driver.apply_load("CC", 1.0, enable_input=True)
    driver.reset_to_safe_state()
    reading = driver.measure()
    assert reading.input_on is False
    assert driver.get_function() is LoadFunction.FIXED


# ----------------------------------------------------------------- library


@pytest.fixture()
def rf() -> BK8500Library:
    lib = BK8500Library(simulated=True, model="8500")
    lib.driver.apply_stabilization_delays = False
    lib.claim_remote_control()
    yield lib
    lib.close_all_load_connections()


def test_library_keywords_measure_and_verify(rf):
    rf.configure_load_protection(max_voltage=20, max_current=5, max_power=100)
    rf.apply_constant_current(2.0, enable_input=True)
    rf.load_current_should_be_within(2.0, 0.01)
    rf.load_voltage_should_be_within(11.9, 0.01)
    rf.load_input_state_should_be("ON")
    rf.load_mode_should_be("CC")
    rf.load_should_report_no_protection_faults()


def test_library_verification_failure_message(rf):
    rf.apply_constant_current(1.0, enable_input=True)
    with pytest.raises(BK8500VerificationError) as excinfo:
        rf.load_current_should_be_within(2.0, 0.01)
    assert "measured" in str(excinfo.value) and "expected" in str(excinfo.value)


def test_library_supports_multiple_loads():
    lib = BK8500Library(auto_connect=False)
    lib.open_load_connection(simulated=True, model="8500", alias="load_a")
    lib.open_load_connection(simulated=True, model="8502", alias="load_b")
    assert lib.get_load_rated_limits()["model"] == "8502"
    lib.switch_load_connection("load_a")
    assert lib.get_load_rated_limits()["model"] == "8500"
    assert lib.get_load_connection_info()["open_aliases"] == ["load_a", "load_b"]
    lib.close_all_load_connections()


def test_library_requires_open_connection():
    lib = BK8500Library(auto_connect=False)
    with pytest.raises(BK8500ConnectionError):
        lib.measure_load_input()


# ------------------------------------------------- serial signal lines (DTR/RTS)


class _FakeSerial:
    """Minimal pyserial stand-in that records configuration and line sequencing."""

    def __init__(self, honour_signal_lines: bool = True, **kwargs):
        self.kwargs = kwargs
        self.is_open = False
        self.port = kwargs.get("port")
        self.timeout = kwargs.get("timeout", 1.0)
        self._honour = honour_signal_lines
        self._dtr = False
        self._rts = False
        self.buffers_reset = 0
        self.events: list[str] = []

    @property
    def dtr(self):
        return self._dtr

    @dtr.setter
    def dtr(self, value):
        self.events.append(f"dtr={bool(value)}:{'open' if self.is_open else 'closed'}")
        self._dtr = bool(value) if self._honour else False

    @property
    def rts(self):
        return self._rts

    @rts.setter
    def rts(self, value):
        self.events.append(f"rts={bool(value)}:{'open' if self.is_open else 'closed'}")
        self._rts = bool(value) if self._honour else False

    def open(self):
        self.events.append("open")
        self.is_open = True

    def reset_input_buffer(self):
        self.buffers_reset += 1

    def reset_output_buffer(self):
        self.buffers_reset += 1

    def close(self):
        self.is_open = False


def _install_fake_serial(monkeypatch, honour_signal_lines: bool = True) -> dict:
    """Install a fake ``serial`` module and return a dict holding the instance."""
    import sys
    import types

    created: dict = {}
    module = types.ModuleType("serial")

    def factory(**kwargs):
        instance = _FakeSerial(honour_signal_lines=honour_signal_lines, **kwargs)
        created["instance"] = instance
        return instance

    module.Serial = factory
    module.SerialException = Exception
    monkeypatch.setitem(sys.modules, "serial", module)
    return created


def test_serial_transport_asserts_dtr_and_rts(monkeypatch):
    """The manual requires both signal lines asserted; do not rely on defaults."""
    from bk8500_load.transport import SerialTransport

    created = _install_fake_serial(monkeypatch)
    transport = SerialTransport("/dev/ttyUSB0", 9600, startup_delay_s=0)
    transport.open()
    assert transport.signal_lines == {"dtr": True, "rts": True}
    assert created["instance"].events[:3] == [
        "dtr=True:closed",
        "rts=True:closed",
        "open",
    ]
    assert "dtr=True:open" in created["instance"].events
    assert "rts=True:open" in created["instance"].events
    assert created["instance"].kwargs["rtscts"] is False
    assert created["instance"].kwargs["dsrdtr"] is False
    assert created["instance"].kwargs["xonxoff"] is False


def test_serial_transport_fails_loudly_when_signal_lines_stay_low(monkeypatch):
    """A silent link must name DTR/RTS rather than surface as a bare timeout."""
    from bk8500_load.transport import SerialTransport

    _install_fake_serial(monkeypatch, honour_signal_lines=False)
    transport = SerialTransport("/dev/ttyUSB0", 9600, startup_delay_s=0)
    with pytest.raises(BK8500ConnectionError) as excinfo:
        transport.open()
    assert "DTR" in str(excinfo.value)


def test_signal_lines_can_be_left_low_when_a_bench_requires_it(monkeypatch):
    from bk8500_load.transport import SerialTransport

    _install_fake_serial(monkeypatch, honour_signal_lines=False)
    transport = SerialTransport("/dev/ttyUSB0", 9600, assert_dtr=False, assert_rts=False, startup_delay_s=0)
    transport.open()
    assert transport.signal_lines == {"dtr": False, "rts": False}



class _TransactionSerial:
    """Serial fake that serves predefined byte chunks after each write."""

    def __init__(self, responses: list[bytes], **kwargs):
        self.kwargs = kwargs
        self.port = kwargs.get("port")
        self.timeout = kwargs.get("timeout", 1.0)
        self.is_open = False
        self.dtr = False
        self.rts = False
        self._responses = bytearray(b"".join(responses))
        self.written: list[bytes] = []

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def reset_input_buffer(self):
        pass

    def reset_output_buffer(self):
        pass

    def write(self, frame):
        self.written.append(bytes(frame))
        return len(frame)

    def flush(self):
        pass

    def read(self, count):
        if not self._responses:
            return b""
        chunk = bytes(self._responses[:count])
        del self._responses[:count]
        return chunk


def _install_transaction_serial(monkeypatch, responses: list[bytes]):
    import sys
    import types

    created = {}
    module = types.ModuleType("serial")

    def factory(**kwargs):
        instance = _TransactionSerial(responses, **kwargs)
        created["instance"] = instance
        return instance

    module.Serial = factory
    module.SerialException = Exception
    monkeypatch.setitem(sys.modules, "serial", module)
    return created


def test_serial_transport_discards_write_echo_then_returns_status(monkeypatch):
    from bk8500_load.transport import SerialTransport

    request = p.build_frame(0, p.Command.SET_REMOTE, bytes([1]))
    status = p.build_frame(0, p.Command.STATUS, bytes([p.StatusCode.SUCCESS]))
    _install_transaction_serial(monkeypatch, [request, status])
    transport = SerialTransport("/dev/ttyUSB0", 9600, timeout_s=0.2, startup_delay_s=0)
    transport.open()
    assert transport.transact(request) == status


def test_serial_transport_rejects_echo_only_write(monkeypatch):
    from bk8500_load.exceptions import BK8500TimeoutError
    from bk8500_load.transport import SerialTransport

    request = p.build_frame(0, p.Command.SET_REMOTE, bytes([1]))
    _install_transaction_serial(monkeypatch, [request])
    transport = SerialTransport("/dev/ttyUSB0", 9600, timeout_s=0.01, startup_delay_s=0)
    transport.open()
    with pytest.raises(BK8500TimeoutError) as excinfo:
        transport.transact(request)
    assert "local echo" in str(excinfo.value)


def test_query_zero_payload_is_not_discarded_as_echo(monkeypatch):
    from bk8500_load.transport import SerialTransport

    # A valid zero-valued GET_MODE response can be byte-for-byte identical to
    # the query, so echo filtering is limited to write commands.
    request = p.build_frame(0, p.Command.GET_MODE)
    _install_transaction_serial(monkeypatch, [request])
    transport = SerialTransport("/dev/ttyUSB0", 9600, timeout_s=0.1, startup_delay_s=0)
    transport.open()
    assert transport.transact(request) == request


def test_serial_transport_discards_query_echo_when_data_frame_follows(monkeypatch):
    from bk8500_load.transport import SerialTransport

    request = p.build_frame(0, p.Command.GET_PRODUCT_INFO)
    payload = b"8500\x00" + bytes([0x84, 0x01]) + b"1687710135"
    response = p.build_frame(0, p.Command.GET_PRODUCT_INFO, payload)
    _install_transaction_serial(monkeypatch, [request, response])
    transport = SerialTransport(
        "/dev/ttyUSB0",
        9600,
        timeout_s=0.2,
        startup_delay_s=0,
        query_echo_grace_s=0.1,
    )
    transport.open()
    assert transport.transact(request) == response


def test_empty_product_info_reply_is_rejected_as_echo_signature():
    load = BK8500Driver.simulated()
    load.connect(identify=False)
    load.transport.transact = lambda frame: bytes(frame)
    with pytest.raises(BK8500ProtocolError) as excinfo:
        load.get_product_info()
    assert "echoed 0x6A request" in str(excinfo.value)


def test_unsupported_baud_rate_is_rejected():
    from bk8500_load.exceptions import BK8500ConfigurationError
    from bk8500_load.transport import SerialTransport

    with pytest.raises(BK8500ConfigurationError) as excinfo:
        SerialTransport("/dev/ttyUSB0", 115200)
    assert "4800, 9600, 19200, 38400" in str(excinfo.value)


def test_supported_baud_rates_match_the_manual():
    from bk8500_load.transport import SUPPORTED_BAUD_RATES

    assert SUPPORTED_BAUD_RATES == (4800, 9600, 19200, 38400)


# ------------------------------------------------- review fixes (Gate 5)


def test_status_tagged_data_reply_is_accepted(driver):
    """R-1: firmware may tag data replies 0x12 instead of echoing the command."""
    real = driver.transport.transact

    def status_tagged(frame):
        response = real(frame)
        if response[2] != p.Command.STATUS:
            return p.build_frame(0, p.Command.STATUS, response[3:24])
        return response

    driver.set_mode("CV")
    driver.transport.transact = status_tagged
    assert driver.get_mode() is LoadMode.CV
    assert driver.response_style == "status_tagged"


def test_bare_success_status_for_a_read_is_not_mistaken_for_data(driver):
    """R-1: 0x80 with an empty payload is ambiguous; refuse rather than guess."""
    driver.transport.transact = lambda frame: p.build_frame(
        0, p.Command.STATUS, bytes([p.StatusCode.SUCCESS])
    )
    with pytest.raises(BK8500ProtocolError) as excinfo:
        driver.get_mode()
    assert "Ambiguous" in str(excinfo.value)


def test_error_status_for_a_read_still_raises_command_error(driver):
    driver.transport.transact = lambda frame: p.build_frame(
        0, p.Command.STATUS, bytes([p.StatusCode.PARAMETER_INCORRECT])
    )
    with pytest.raises(BK8500CommandError):
        driver.get_mode()


def test_echo_reply_style_is_recorded(driver):
    driver.get_mode()
    assert driver.response_style == "echo"


def test_timeouts_are_retried(monkeypatch):
    """R-2: a timeout is transient on a TTL link and must be retried."""
    from bk8500_load.exceptions import BK8500TimeoutError

    load = BK8500Driver.simulated(retries=2, retry_delay_s=0)
    load.connect()
    calls = {"n": 0}

    def timing_out(frame):
        calls["n"] += 1
        raise BK8500TimeoutError("short read")

    monkeypatch.setattr(load.transport, "transact", timing_out)
    with pytest.raises(BK8500TimeoutError):
        load.get_mode()
    assert calls["n"] == 3


def test_reply_from_another_address_is_rejected(driver):
    """R-5: on a multi-drop bus a stranger's reply must not be accepted."""
    driver.transport.transact = lambda frame: p.build_frame(7, p.Command.GET_MODE, bytes([1]))
    with pytest.raises(BK8500ProtocolError) as excinfo:
        driver.get_mode()
    assert "address" in str(excinfo.value)


def test_invalid_list_step_leaves_the_instrument_untouched(driver):
    """R-3: validation is all-or-nothing, so no half-written profile survives."""
    driver.configure_list("CC", [(1.0, 0.1), (2.0, 0.1)])
    with pytest.raises(BK8500ValidationError):
        driver.configure_list("CC", [(1.0, 0.1), (2.0, 0.1), (99.0, 0.1)])
    assert driver.get_list_step_count() == 2
    assert sorted(driver.transport.list_steps) == [1, 2]


def test_invalid_list_name_is_caught_before_any_step_is_written(driver):
    with pytest.raises(BK8500ValidationError):
        driver.configure_list("CC", [(1.0, 0.1)], name="ELEVENCHARS")
    assert driver.get_list_step_count() == 0


def test_stabilization_delays_are_applied(monkeypatch):
    """R-6: the contract's declared delays are behaviour, not advice."""
    from bk8500_load import driver as driver_module

    load = BK8500Driver.simulated()
    load.connect()
    load.set_remote_control(True)
    slept: list[float] = []
    monkeypatch.setattr(driver_module.time, "sleep", slept.append)
    load.set_input_state(True)
    assert slept == [driver_module.STABILIZATION_DELAYS_S["input_state"]]


def test_stabilization_delays_can_be_disabled(monkeypatch):
    from bk8500_load import driver as driver_module

    load = BK8500Driver.simulated(apply_stabilization_delays=False)
    load.connect()
    load.set_remote_control(True)
    slept: list[float] = []
    monkeypatch.setattr(driver_module.time, "sleep", slept.append)
    load.set_input_state(True)
    assert slept == []


def test_booleans_are_not_accepted_as_setpoints(driver):
    with pytest.raises(BK8500ValidationError) as excinfo:
        driver.set_setpoint("CC", True)
    assert "boolean" in str(excinfo.value)


def test_product_info_exposes_raw_firmware_bytes(driver):
    info = driver.get_product_info()
    assert info.firmware_raw == (1, 5)
    assert info.as_dict()["firmware_raw"] == [1, 5]


def test_closing_the_current_connection_does_not_adopt_another():
    """A keyword after the close must not silently act on a different load."""
    lib = BK8500Library(auto_connect=False)
    lib.open_load_connection(simulated=True, model="8500", alias="load_a")
    lib.open_load_connection(simulated=True, model="8502", alias="load_b")
    lib.close_load_connection("load_b")
    with pytest.raises(BK8500ConnectionError):
        lib.measure_load_input()
    lib.switch_load_connection("load_a")
    assert lib.get_load_rated_limits()["model"] == "8500"
    lib.close_all_load_connections()


def test_installed_contract_is_locatable():
    """R-4: an installed driver must ship its own contract."""
    import bk8500_load

    assert bk8500_load.contract_path().is_file()
    assert bk8500_load.lock_path().is_file()


def test_duplicate_connection_alias_is_rejected_without_replacing_original():
    lib = BK8500Library(auto_connect=False)
    lib.open_load_connection(simulated=True, model="8500", alias="load")
    original = lib.driver
    with pytest.raises(BK8500ConnectionError) as excinfo:
        lib.open_load_connection(simulated=True, model="8502", alias="load")
    assert "already open" in str(excinfo.value)
    assert lib.driver is original
    lib.close_all_load_connections()


def test_failed_identification_closes_transport():
    class FailingIdentityTransport(SimulatedTransport):
        def transact(self, frame: bytes) -> bytes:
            raise BK8500ProtocolError("identity reply malformed")

    transport = FailingIdentityTransport(model="8500")
    load = BK8500Driver(transport, retries=0)
    with pytest.raises(BK8500ProtocolError):
        load.connect(identify=True)
    assert not transport.is_open


# ---------------------------------------------------------- releases 26.13-26.14


def test_single_step_list_is_rejected_locally_before_protocol_writes(driver):
    previous_frames = len(driver.transport.frame_log)
    with pytest.raises(BK8500ValidationError) as excinfo:
        driver.configure_list("CC", [(0.01, 0.1)])
    assert "at least 2 steps" in str(excinfo.value)
    assert len(driver.transport.frame_log) == previous_frames


def test_simulator_rejects_wire_level_single_step_count(driver):
    response = driver.transport.transact(
        p.build_frame(driver.address, p.Command.SET_LIST_STEP_COUNT, p.encode_int(1, 2))
    )
    assert response[2] == p.Command.STATUS
    assert response[3] == p.StatusCode.PARAMETER_INCORRECT


# ---------------------------------------------------------- release 26.12


def test_list_partition_capacity_is_validated_before_profile_writes(driver):
    driver.set_list_partition(8)
    previous_frames = len(driver.transport.frame_log)
    with pytest.raises(BK8500ValidationError) as excinfo:
        driver.configure_list("CC", [(0.01, 0.1)] * 121)
    assert "partition 8 allows at most 120" in str(excinfo.value)
    # One read of the current partition is allowed; no list-write command may run.
    written = [request[2] for request, _ in driver.transport.frame_log[previous_frames:]]
    assert written == [p.Command.GET_LIST_PARTITION]


def test_list_save_reconfigure_and_recall_roundtrip(driver):
    driver.set_list_partition(8)
    saved = [(0.01, 0.1), (0.04, 0.2)]
    driver.configure_list("CC", saved, name="RFSAVED")
    driver.save_list_file(8)
    driver.configure_list("CC", [(0.02, 0.1), (0.03, 0.1)], name="CHANGED")
    assert driver.get_list_step_count() == 2
    driver.recall_list_file(8)
    assert driver.get_list_step_count() == 2
    restored = driver.get_list_step("CC", 2)
    assert restored.level == pytest.approx(0.04)
    assert restored.dwell_s == pytest.approx(0.2)


def test_persistent_operations_apply_dedicated_settle_delays(monkeypatch):
    from bk8500_load import driver as driver_module

    load = BK8500Driver.simulated(model="8500")
    load.connect()
    load.set_remote_control(True)
    load.set_list_partition(8)
    load.configure_list("CC", [(0.01, 0.1), (0.02, 0.1)])
    slept: list[float] = []
    monkeypatch.setattr(driver_module.time, "sleep", slept.append)

    load.save_list_file(8)
    load.recall_list_file(8)
    load.save_settings(25)
    load.recall_settings(25)

    assert slept == [
        driver_module.STABILIZATION_DELAYS_S["save_list_file"],
        driver_module.STABILIZATION_DELAYS_S["recall_list_file"],
        driver_module.STABILIZATION_DELAYS_S["save_settings"],
        driver_module.STABILIZATION_DELAYS_S["recall_settings"],
    ]


def test_list_step_count_rejection_contains_profile_context(driver, monkeypatch):
    original_write = driver._write

    def reject_count(command, payload=b""):
        if command == p.Command.SET_LIST_STEP_COUNT:
            raise BK8500CommandError("Command 0x3E rejected", status=0xA0)
        return original_write(command, payload)

    monkeypatch.setattr(driver, "_write", reject_count)
    with pytest.raises(BK8500CommandError) as excinfo:
        driver.configure_list("CC", [(0.01, 0.1), (0.02, 0.1)])
    message = str(excinfo.value)
    assert "step count=2" in message
    assert "partition=8" in message
    assert "capacity=120" in message

# ------------------------------------------------------ baud-rate auto detection


def test_ordered_baud_rates_prefers_requested_rate_and_deduplicates():
    from bk8500_load.driver import _ordered_baud_rates

    assert _ordered_baud_rates(19200, [9600, 19200, 4800, 9600]) == (
        19200,
        9600,
        4800,
    )


def test_ordered_baud_rates_rejects_unsupported_before_open():
    from bk8500_load.driver import _ordered_baud_rates
    from bk8500_load.exceptions import BK8500ConfigurationError

    with pytest.raises(BK8500ConfigurationError) as excinfo:
        _ordered_baud_rates(115200, [9600])
    assert "Supported rates" in str(excinfo.value)


class _ProbeSerialObject:
    def __init__(self, timeout: float):
        self.timeout = timeout


class _ProbeTransport:
    def __init__(self, baudrate: int, timeout_s: float):
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self._serial = _ProbeSerialObject(timeout_s)
        self.close_count = 0

    def close(self):
        self.close_count += 1


class _ProbeCandidate:
    def __init__(self, baudrate: int, timeout_s: float, outcomes):
        self.transport = _ProbeTransport(baudrate, timeout_s)
        self.outcomes = list(outcomes)
        self.calls: list[str] = []
        self.retries = 0
        self.retry_delay_s = 0.0
        self.detected_baudrate = baudrate
        self.baudrate_probe_attempts = ()

    def _next(self):
        if not self.outcomes:
            raise AssertionError("Probe candidate has no configured response")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def connect(self, identify=True):
        assert identify is True
        self.calls.append("get_product_info")
        return self._next()

    def get_product_info(self):
        self.calls.append("get_product_info")
        return self._next()


def _install_probe_candidates(monkeypatch, outcome_map):
    created = []

    def factory(
        cls,
        port,
        baudrate=9600,
        model=None,
        address=0,
        timeout_s=1.0,
        assert_dtr=True,
        assert_rts=True,
        **kwargs,
    ):
        candidate = _ProbeCandidate(
            baudrate,
            timeout_s,
            outcome_map[baudrate],
        )
        created.append(candidate)
        return candidate

    monkeypatch.setattr(BK8500Driver, "on_serial_port", classmethod(factory))
    return created


def test_baud_detection_falls_back_and_confirms_identity(monkeypatch):
    from bk8500_load.enums import ProductInfo
    from bk8500_load.exceptions import BK8500TimeoutError

    info = ProductInfo("8500", "1687710135", "1.84", (1, 0x84))
    created = _install_probe_candidates(
        monkeypatch,
        {
            9600: [BK8500TimeoutError("no response")],
            4800: [info, info],
        },
    )

    selected, identity, attempts = BK8500Driver.connect_serial_with_baud_detection(
        port="COM12",
        preferred_baudrate=9600,
        baudrate_candidates=[4800],
        timeout_s=2.0,
        probe_timeout_s=0.1,
        retries=3,
        retry_delay_s=0.02,
        inter_probe_delay_s=0,
    )

    assert identity == info
    assert selected is created[1]
    assert created[0].transport.close_count >= 1
    assert selected.calls == ["get_product_info", "get_product_info"]
    assert selected.transport.timeout_s == 2.0
    assert selected.transport._serial.timeout == 2.0
    assert selected.retries == 3
    assert selected.detected_baudrate == 4800
    assert [attempt["baudrate"] for attempt in attempts] == [9600, 4800]
    assert [attempt["result"] for attempt in attempts] == ["FAIL", "PASS"]
    # Detection is read-only: the candidate interface was asked only for identity.
    assert all(candidate.calls == ["get_product_info"] for candidate in created[:1])


def test_baud_detection_rejects_inconsistent_identity_and_closes(monkeypatch):
    from bk8500_load.enums import ProductInfo
    from bk8500_load.exceptions import BK8500ConnectionError

    first = ProductInfo("8500", "SERIAL1", "1.84", (1, 0x84))
    second = ProductInfo("8500", "SERIAL2", "1.84", (1, 0x84))
    created = _install_probe_candidates(monkeypatch, {9600: [first, second]})

    with pytest.raises(BK8500ConnectionError) as excinfo:
        BK8500Driver.connect_serial_with_baud_detection(
            port="COM12",
            preferred_baudrate=9600,
            baudrate_candidates=[],
            inter_probe_delay_s=0,
        )
    assert "not repeatable" in str(excinfo.value)
    assert created[0].transport.close_count >= 1


def test_baud_detection_all_failures_are_reported_and_closed(monkeypatch):
    from bk8500_load.exceptions import BK8500ConnectionError, BK8500TimeoutError

    created = _install_probe_candidates(
        monkeypatch,
        {
            9600: [BK8500TimeoutError("timeout at 9600")],
            19200: [BK8500TimeoutError("timeout at 19200")],
        },
    )
    with pytest.raises(BK8500ConnectionError) as excinfo:
        BK8500Driver.connect_serial_with_baud_detection(
            port="COM12",
            preferred_baudrate=9600,
            baudrate_candidates=[19200],
            inter_probe_delay_s=0,
        )
    message = str(excinfo.value)
    assert "9600" in message and "19200" in message
    assert all(candidate.transport.close_count >= 1 for candidate in created)


def test_library_auto_baud_mode_delegates_and_reports_selected_rate(monkeypatch):
    from bk8500_load.enums import ProductInfo

    info = ProductInfo("8500", "1687710135", "1.84", (1, 0x84))
    selected = BK8500Driver.simulated(model="8500", apply_stabilization_delays=False)
    selected.connect()
    selected.transport.baudrate = 19200
    selected.detected_baudrate = 19200
    selected.baudrate_probe_attempts = (
        {"baudrate": 9600, "result": "FAIL", "error": "timeout"},
        {"baudrate": 19200, "result": "PASS", "identity": info.as_dict()},
    )
    captured = {}

    def detect(cls, **kwargs):
        captured.update(kwargs)
        return selected, info, selected.baudrate_probe_attempts

    monkeypatch.setattr(
        BK8500Driver,
        "connect_serial_with_baud_detection",
        classmethod(detect),
    )

    lib = BK8500Library(auto_connect=False)
    alias = lib.open_load_connection(
        port="COM12",
        baudrate="AUTO",
        baudrate_candidates="4800,19200,38400",
    )
    assert alias == "default"
    assert captured["preferred_baudrate"] == 9600
    assert captured["baudrate_candidates"] == (4800, 19200, 38400)
    connection = lib.get_load_connection_info()
    assert connection["baudrate"] == 19200
    assert connection["baudrate_auto_detected"] is True
    assert len(connection["baudrate_probe_attempts"]) == 2
    lib.close_all_load_connections(safe=False)


def test_simulation_mode_bypasses_baud_probe(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("serial baud detection must not run in simulation")

    monkeypatch.setattr(
        BK8500Driver,
        "connect_serial_with_baud_detection",
        classmethod(unexpected),
    )
    lib = BK8500Library(auto_connect=False)
    lib.open_load_connection(simulated=True, baudrate="AUTO")
    assert lib.get_load_product_information()["model"] == "8500"
    lib.close_all_load_connections(safe=False)


def test_baud_detection_rejects_invalid_probe_timeout_before_open(monkeypatch):
    from bk8500_load.exceptions import BK8500ConfigurationError

    opened = {"value": False}

    def factory(*args, **kwargs):
        opened["value"] = True
        raise AssertionError("port must not be opened")

    monkeypatch.setattr(BK8500Driver, "on_serial_port", classmethod(factory))
    with pytest.raises(BK8500ConfigurationError):
        BK8500Driver.connect_serial_with_baud_detection(
            port="COM12",
            probe_timeout_s=0.0,
        )
    assert opened["value"] is False


def test_fixed_numeric_baud_preserves_single_rate_connection(monkeypatch):
    captured = {}

    def on_serial(
        cls,
        port,
        baudrate=9600,
        model=None,
        address=0,
        timeout_s=1.0,
        assert_dtr=True,
        assert_rts=True,
        **kwargs,
    ):
        captured.update(port=port, baudrate=baudrate, timeout_s=timeout_s)
        return BK8500Driver.simulated(model=model or "8500", apply_stabilization_delays=False)

    def unexpected(*args, **kwargs):
        raise AssertionError("automatic detection must remain disabled by default")

    monkeypatch.setattr(BK8500Driver, "on_serial_port", classmethod(on_serial))
    monkeypatch.setattr(
        BK8500Driver,
        "connect_serial_with_baud_detection",
        classmethod(unexpected),
    )
    lib = BK8500Library(auto_connect=False)
    lib.open_load_connection(port="COM12", baudrate=19200, model="8500")
    assert captured == {"port": "COM12", "baudrate": 19200, "timeout_s": 1.0}
    assert lib.get_load_connection_info()["baudrate_auto_detected"] is False
    lib.close_all_load_connections(safe=False)

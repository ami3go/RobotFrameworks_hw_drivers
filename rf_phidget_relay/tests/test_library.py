from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from rf_phidget_relay import PhidgetRelayLibrary


class FakeOutput:
    instances = []

    def __init__(self):
        self.serial = None
        self.channel = None
        self.state = False
        self.opened = False
        self.closed = False
        FakeOutput.instances.append(self)

    def setDeviceSerialNumber(self, value): self.serial = value
    def setChannel(self, value): self.channel = value
    def openWaitForAttachment(self, _timeout): self.opened = True
    def setState(self, value): self.state = bool(value)
    def getState(self): return self.state
    def close(self): self.closed = True


@pytest.fixture
def relay():
    FakeOutput.instances = []
    obj = PhidgetRelayLibrary(output_factory=FakeOutput, sleep_function=lambda _s: None)
    obj.connect_relays(111111, 222222)
    return obj


def test_maps_two_devices_to_eight_logical_channels(relay):
    assert [(o.serial, o.channel) for o in FakeOutput.instances] == [
        (111111, 0), (111111, 1), (111111, 2), (111111, 3),
        (222222, 0), (222222, 1), (222222, 2), (222222, 3),
    ]


def test_connect_opens_all_by_default(relay):
    assert relay.get_all_relay_states() == {channel: "OPEN" for channel in range(1, 9)}


def test_open_close_and_readback(relay):
    relay.close_relay(5)
    assert relay.get_relay_state(5) == "CLOSED"
    relay.open_relay(5)
    assert relay.get_relay_state(5) == "OPEN"


def test_pattern(relay):
    relay.set_relay_pattern("10000001")
    assert relay.get_relay_state(1) == "CLOSED"
    assert relay.get_relay_state(2) == "OPEN"
    assert relay.get_relay_state(8) == "CLOSED"


def test_invalid_pattern_causes_no_partial_write(relay):
    relay.close_relay(3)
    before = relay.get_all_relay_states()
    with pytest.raises(ValueError):
        relay.set_relay_pattern("1002")
    assert relay.get_all_relay_states() == before


def test_pulse_returns_to_open(relay):
    relay.pulse_relay(2, 0)
    assert relay.get_relay_state(2) == "OPEN"


@pytest.mark.parametrize("channel", [0, 9, "bad"])
def test_invalid_channels_rejected(relay, channel):
    with pytest.raises(ValueError):
        relay.close_relay(channel)


def test_duplicate_serial_rejected():
    obj = PhidgetRelayLibrary(output_factory=FakeOutput)
    with pytest.raises(ValueError):
        obj.connect_relays(123, 123)


def test_active_low_translation():
    FakeOutput.instances = []
    obj = PhidgetRelayLibrary(active_high=False, output_factory=FakeOutput)
    obj.connect_relays(111, 222)
    obj.close_relay(1)
    assert FakeOutput.instances[0].state is False
    assert obj.get_relay_state(1) == "CLOSED"


def test_disconnect_opens_and_closes_handles(relay):
    relay.close_all_relays()
    relay.disconnect_relays()
    assert all(output.state is False and output.closed for output in FakeOutput.instances)


def test_connection_status_and_driver_information(relay):
    assert relay.get_connection_status() == "CONNECTED"
    info = relay.get_driver_information()
    assert info["version"] == "26.3"
    assert info["device_serials"] == [111111, 222222]
    relay.disconnect_relays()
    assert relay.get_connection_status() == "DISCONNECTED"


def test_emergency_open_all_relays(relay):
    relay.close_all_relays()
    relay.emergency_open_all_relays()
    assert set(relay.get_all_relay_states().values()) == {"OPEN"}


def test_failed_attachment_closes_handle_that_failed_during_open():
    class FailingOutput(FakeOutput):
        def openWaitForAttachment(self, _timeout):
            if self.channel == 2:
                raise RuntimeError("attach failed")
            self.opened = True

    FailingOutput.instances = []
    obj = PhidgetRelayLibrary(output_factory=FailingOutput)
    with pytest.raises(RuntimeError, match="attach failed"):
        obj.connect_relays(111, 222)
    assert obj.get_connection_status() == "DISCONNECTED"
    assert all(item.closed for item in FailingOutput.instances)


def test_rfds_contract_covers_every_robot_keyword():
    root = Path(__file__).parents[1]
    contract = yaml.safe_load((root / "ai" / "phidget_relay_ai_contract.yaml").read_text(encoding="utf-8"))
    contracted = {item["name"] for item in contract["capabilities"]}
    implemented = {
        value.robot_name
        for value in vars(PhidgetRelayLibrary).values()
        if callable(value) and getattr(value, "robot_name", None)
    }
    assert contracted == implemented
    assert contract["schema"] == "RFDS-017"
    assert contract["schema_version"] == "3.0"

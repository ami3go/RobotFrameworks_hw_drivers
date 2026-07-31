"""Execute the complete public keyword API against the in-process instrument.

The hardware Robot suite performs the same API coverage on a physical load. This
pytest regression makes package builds fail when any public keyword is omitted
from executable coverage or cannot complete against the protocol simulator.
"""

from __future__ import annotations

from bk8500_load.library import BK8500Library


def test_every_public_keyword_executes_against_simulated_device():
    library = BK8500Library(auto_connect=False)
    executed: set[str] = set()

    def call(name, function, *args, **kwargs):
        result = function(*args, **kwargs)
        executed.add(name)
        return result

    call(
        "Open Load Connection",
        library.open_load_connection,
        simulated=True,
        model="8500",
        alias="hardware",
        source_voltage=12.0,
        source_resistance=0.05,
    )
    call("Get Load Product Information", library.get_load_product_information)
    call("Get Load Rated Limits", library.get_load_rated_limits)
    call("Claim Remote Control", library.claim_remote_control)
    call("Set Local Key Enabled", library.set_local_key_enabled, False)
    call("Set Local Key Enabled", library.set_local_key_enabled, True)
    call("Load Input Off", library.load_input_off)
    call("Set Remote Sense", library.set_remote_sense, True)
    call("Get Remote Sense", library.get_remote_sense)
    call("Set Remote Sense", library.set_remote_sense, False)
    call("Configure Load Protection", library.configure_load_protection, 120.0, 30.0, 300.0)
    call("Get Load Protection Limits", library.get_load_protection_limits)

    for mode, value in (("CC", 0.05), ("CV", 1.0), ("CW", 0.5), ("CR", 1000.0)):
        call("Set Load Mode", library.set_load_mode, mode)
        call("Get Load Mode", library.get_load_mode)
        call("Set Load Setpoint", library.set_load_setpoint, mode, value)
        call("Get Load Setpoint", library.get_load_setpoint, mode)

    call("Apply Constant Current", library.apply_constant_current, 0.05, False)
    call("Apply Constant Voltage", library.apply_constant_voltage, 1.0, False)
    call("Apply Constant Power", library.apply_constant_power, 0.5, False)
    call("Apply Constant Resistance", library.apply_constant_resistance, 1000.0, False)
    call("Set Load Function", library.set_load_function, "FIXED")
    call("Set Load Function Unchecked", library.set_load_function_unchecked, "FIXED")
    call("Get Load Function", library.get_load_function)
    call("Configure Load Transient", library.configure_load_transient, "CC", 0.02, 0.1, 0.05, 0.2)
    call("Get Load Transient", library.get_load_transient, "CC")
    call("Set Load Trigger Source", library.set_load_trigger_source, "BUS")
    call("Get Load Trigger Source", library.get_load_trigger_source)
    call("Trigger Load", library.trigger_load)
    call("Set Load Trigger Source", library.set_load_trigger_source, "IMMEDIATE")

    steps = [(0.01, 0.1), (0.03, 0.2)]
    call("Configure Load List", library.configure_load_list, "CC", steps, "ONCE", "RFTEST")
    call("Get Load List Step", library.get_load_list_step, "CC", 1)
    call("Get Load List Step Count", library.get_load_list_step_count)
    call("Save Load List File", library.save_load_list_file, 8)
    call("Recall Load List File", library.recall_load_list_file, 8)
    call("Set Battery Cutoff Voltage", library.set_battery_cutoff_voltage, 0.5)
    call("Get Battery Cutoff Voltage", library.get_battery_cutoff_voltage)
    call("Set Load On Timer", library.set_load_on_timer, 2, True)
    call("Get Load On Timer", library.get_load_on_timer)
    call("Save Load Settings", library.save_load_settings, 25)
    call("Set Load Setpoint", library.set_load_setpoint, "CC", 0.02)
    call("Recall Load Settings", library.recall_load_settings, 25)

    call("Apply Constant Current", library.apply_constant_current, 0.05, False)
    call("Load Input On", library.load_input_on)
    call("Load Input State Should Be", library.load_input_state_should_be, "ON")
    call("Load Input Off", library.load_input_off)
    reading = call("Measure Load Input", library.measure_load_input)
    voltage = call("Get Load Voltage", library.get_load_voltage)
    current = call("Get Load Current", library.get_load_current)
    power = call("Get Load Power", library.get_load_power)
    call("Wait Until Load Reading Is Stable", library.wait_until_load_reading_is_stable, "current", 0.1, 0.0, 1.0, 0.0)
    call("Load Voltage Should Be Within", library.load_voltage_should_be_within, voltage, 0.01)
    call("Load Current Should Be Within", library.load_current_should_be_within, current, 0.01)
    call("Load Power Should Be Within", library.load_power_should_be_within, power, 0.01)
    call("Load Should Report No Protection Faults", library.load_should_report_no_protection_faults)
    call("Load Input State Should Be", library.load_input_state_should_be, "OFF")
    call("Set Load Mode", library.set_load_mode, "CC")
    call("Load Mode Should Be", library.load_mode_should_be, "CC")
    call("Get Load Connection Info", library.get_load_connection_info)

    call("Open Load Connection", library.open_load_connection, simulated=True, model="8500", alias="secondary")
    call("Switch Load Connection", library.switch_load_connection, "hardware")
    call("Switch Load Connection", library.switch_load_connection, "secondary")
    call("Close Load Connection", library.close_load_connection, "secondary")
    call("Switch Load Connection", library.switch_load_connection, "hardware")
    call("Release Remote Control", library.release_remote_control)
    call("Claim Remote Control", library.claim_remote_control)
    call("Reset Load To Safe State", library.reset_load_to_safe_state)
    call("Close All Load Connections", library.close_all_load_connections)

    public = {
        getattr(attribute, "robot_name")
        for attribute in vars(BK8500Library).values()
        if getattr(attribute, "robot_name", None)
    }
    assert executed == public, f"Missing executable keyword coverage: {sorted(public - executed)}"
    assert reading["input_on"] is False

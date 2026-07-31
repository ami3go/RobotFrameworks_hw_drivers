from bk8500b import BK8500B, DriverConfig, OperatingMode

with BK8500B(DriverConfig(port="COM5")) as load:
    assert not load.get_input_enabled()
    load.set_operating_mode(OperatingMode.VOLTAGE)
    print(load.set_voltage_setpoint(5.0))

    load.set_operating_mode(OperatingMode.POWER)
    print(load.set_power_setpoint(1.0))

    load.set_operating_mode(OperatingMode.RESISTANCE)
    print(load.set_resistance_setpoint(100.0))

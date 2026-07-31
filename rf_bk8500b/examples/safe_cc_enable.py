"""Commission only with limits verified for the connected DUT."""
from bk8500b import BK8500B, DriverConfig, OperatingMode, SafeEnableConfig

with BK8500B(DriverConfig(port="COM5")) as load:
    try:
        result = load.configure_and_enable(
            SafeEnableConfig(
                mode=OperatingMode.CURRENT,
                setpoint=0.05,
                current_limit_a=0.10,
                power_limit_w=2.0,
            )
        )
        print(result)
    finally:
        try:
            load.set_input_enabled(False)
        except Exception as exc:
            print(f"WARNING: input OFF could not be verified: {exc}")

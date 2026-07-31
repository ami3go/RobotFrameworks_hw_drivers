from bk8500b import BK8500B, DriverConfig, DynamicMode, TransientConfig

with BK8500B(DriverConfig(port="COM5")) as load:
    load.configure_transient(
        TransientConfig(
            high_level=1.0,
            high_dwell_s=0.1,
            low_level=0.1,
            low_dwell_s=0.1,
            slew_a_per_us=0.5,
            mode=DynamicMode.CONTINUOUS,
        )
    )
    print(load.get_transient_config())

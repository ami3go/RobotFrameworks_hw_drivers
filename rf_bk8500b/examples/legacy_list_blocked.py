"""Documents the current validation boundary; it does not run a list."""
from bk8500b import BK8500B, DriverConfig, ListConfig, Protocol, UnsupportedFeatureError

with BK8500B(DriverConfig(port="COM5", protocol=Protocol.LEGACY)) as load:
    try:
        load.configure_list(ListConfig(steps=()))
    except UnsupportedFeatureError as exc:
        print(f"Expected validation gate: {exc}")

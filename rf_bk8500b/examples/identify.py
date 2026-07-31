from bk8500b import BK8500B, DriverConfig

with BK8500B(DriverConfig(port="COM9")) as load:
    print(load.identify())
    print(load.get_capabilities())

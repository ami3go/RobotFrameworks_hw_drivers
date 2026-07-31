from bk8500b import BK8500B, DriverConfig

with BK8500B(DriverConfig(port="COM5")) as load:
    result = load.measure_all()
    print(f"{result.voltage.value:.6g} V")
    print(f"{result.current.value:.6g} A")
    print(f"{result.power.value:.6g} W")

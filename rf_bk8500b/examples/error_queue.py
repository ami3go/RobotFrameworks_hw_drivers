from bk8500b import BK8500B, DriverConfig

with BK8500B(DriverConfig(port="COM5")) as load:
    for error in load.drain_error_queue():
        print(error.code, error.message)

import time

from bk8500b import BK8500B, DriverConfig, ProtectionTrippedError

with BK8500B(DriverConfig(port="COM5")) as load:
    while True:
        status = load.get_device_status()
        print(status)
        if status.protection_flags:
            raise ProtectionTrippedError(
                "Protection detected; stop the external test sequence",
                context={"flags": int(status.protection_flags)},
            )
        time.sleep(1.0)

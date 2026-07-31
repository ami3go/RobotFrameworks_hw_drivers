import time

from bk8500b import BK8500B, DriverConfig, ReconnectPolicy

config = DriverConfig(
    port="COM5",
    reconnect=ReconnectPolicy(enabled=True, max_attempts=3, total_deadline_s=15.0),
)

with BK8500B(config) as load:
    while True:
        report = load.health_check()
        print(report.to_dict())
        if not report.healthy and config.reconnect.enabled:
            try:
                load.reconnect()
            except Exception as exc:
                print(f"Reconnect failed: {exc}")
                break
        time.sleep(5.0)

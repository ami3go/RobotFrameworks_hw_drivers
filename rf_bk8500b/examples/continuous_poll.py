import signal
import time

from bk8500b import BK8500B, DriverConfig

running = True

def stop(*_args):
    global running
    running = False

signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

with BK8500B(DriverConfig(port="COM5")) as load:
    while running:
        snapshot = load.measure_all()
        print(snapshot.voltage.value, snapshot.current.value, snapshot.power.value)
        time.sleep(1.0)

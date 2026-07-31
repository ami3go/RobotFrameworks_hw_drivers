from eresistor_driver import EResistorClient

with EResistorClient("192.168.7.50") as dev:
    dev.download_calibration()
    result = dev.set_resistance(1, 10_000.0)
    print(result)

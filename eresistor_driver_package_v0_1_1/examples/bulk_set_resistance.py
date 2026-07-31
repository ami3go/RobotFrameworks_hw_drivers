from eresistor_driver import EResistorClient

with EResistorClient("192.168.7.50") as dev:
    dev.download_calibration()
    results = dev.set_resistances({1: 1_000.0, 2: 10_000.0, 4: 100_000.0})
    for r in results:
        print(r)

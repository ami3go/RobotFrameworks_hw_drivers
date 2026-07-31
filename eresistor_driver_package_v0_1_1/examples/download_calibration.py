from eresistor_driver import EResistorClient

with EResistorClient("192.168.7.50") as dev:
    cal = dev.download_calibration()
    dev.save_calibration("calibration.json")
    print(f"Downloaded channels: {sorted(cal.channels)}")

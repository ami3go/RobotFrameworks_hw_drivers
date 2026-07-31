from eresistor_driver import EResistorClient

with EResistorClient("192.168.7.50") as dev:
    dev.download_calibration()
    dev.load_temperature_table(channel=1, path="ntc_10k.csv")
    result = dev.set_temperature(channel=1, temperature_c=25.0)
    print(result)

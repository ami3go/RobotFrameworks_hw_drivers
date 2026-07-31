from eresistor_driver import EResistorClient

with EResistorClient("192.168.7.50") as dev:
    dev.set_mask(1, "0001")
    print("CH1 mask:", dev.get_mask(1))

from eresistor_driver import EResistorClient

with EResistorClient("192.168.7.50") as dev:
    print(dev.idn())
    print(dev.get_status())

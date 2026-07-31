from eresistor_driver import EResistorClient

with EResistorClient("192.168.7.50") as dev:
    dev.download_calibration()
    dev.load_temperature_table_for_all("ntc_10k.csv")
    sim = dev.create_curve_simulation(channel=1, path="temperature_profile.csv", repeat=3)
    sim.run()
    sim.export_log_csv("simulation_log.csv")

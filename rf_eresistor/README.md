# RF E-Resistor

Robot Framework library for the OpenBench/RP2040 + W5500 E-Resistor programmable resistor matrix. Release **26.02** wraps the bundled and reviewed Python driver `eresistor-driver 0.1.1` without changing its SCPI, calibration, solver, safety, or HTTP fallback logic.

## Capabilities

- Connect and identify the board over SCPI/TCP (default port 5025)
- Control eight 16-bit matrix channels by mask
- Open all outputs safely
- Download, cache, save, and load calibration
- Calculate and set the closest resistance
- Apply multiple channel values atomically
- Convert temperature tables into resistance settings
- Discover boards, inspect errors/status, use raw SCPI, watchdog and metrics
- Return Robot-friendly dictionaries for result assertions
- Provide a locked, machine-readable RFDS-017 AI driver contract covering every Robot keyword

## Install

Python 3.10 or newer is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux:   source .venv/bin/activate
python -m pip install -e ".[test,yaml]"
```

## Minimal real-hardware test

```robot
*** Settings ***
Library      rf_eresistor    host=192.168.0.55
Suite Setup     Connect To EResistor    all_off_on_connect=${True}
Suite Teardown  Disconnect From EResistor

*** Test Cases ***
Set Ten Kilohms On Channel One
    Download EResistor Calibration
    ${result}=    Set EResistor Resistance    1    10000
    Log    mask=${result}[mask], actual=${result}[calculated_ohm] ohm
```

Run it with `robot --outputdir results examples/02_set_resistance.robot`.

## Safety

`0000` opens a channel. Bit 0 maps to Q16 (the lowest-value branch), bit 15 to Q1. `1` activates a MOSFET branch. The library defaults to `ALL:OFF` when it disconnects and can also open every output immediately on connect. Network loss cannot guarantee physical safe state without firmware-side watchdog support.

Do not connect a DUT until you have run the read-only identity example and verified the channel/mask mapping on your hardware. Use `force=True` only when intentionally overriding simulation-channel locking; it does not bypass resistance or active-bit safety limits.

## Documentation

- [Keyword reference](docs/keyword_reference.md)
- [Installation and PyCharm/Robot guide](guide/pycharm_robot_framework_setup.md)
- [Hardware setup](guide/hardware_setup.md)
- [Examples](examples/README.md)
- [Release history](history/v26.01.md)
- [Implementation review](review/v26.01_code_review.md)
- [AI driver contract](ai/README.md)
- [Release 26.02 history](history/v26.02.md)
- [Release 26.02 compliance review](review/v26.02_code_review.md)

Generate Robot's HTML keyword documentation with:

```bash
python -m robot.libdoc rf_eresistor docs/rf_eresistor.html
```

The `docs/` folder is GitHub Pages ready. Enable Pages from the repository root or publish that folder with your preferred workflow.

## Test

```bash
python -m pytest
python -m robot --outputdir results tests/robot
```

Hardware examples are deliberately not part of the offline test suite.

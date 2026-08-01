# Installing the RobotFrameworks_hw_drivers packages

This repository contains eight independent Robot Framework hardware-instrument
driver packages. Each ships as its own installable Python distribution with
its own `pyproject.toml`, so they can be installed together in one virtual
environment or individually as needed.

| Package | Distribution name | Instrument | Requires Python |
|---|---|---|---|
| `rf_bk8500b` | `robotframework-bk8500b` | B&K Precision 8500B electronic load | >=3.10 |
| `rf_bk8500_load` | `bk8500-load` | B&K Precision 8500 series DC load | >=3.9 |
| `rf_eresistor` | `rf-eresistor` | OpenBench E-Resistor | >=3.10 |
| `rf_hp34401a` | `rf-hp34401a` | HP/Agilent/Keysight 34401A DMM | >=3.10 |
| `rf_keysight_n6700` | `robotframework-keysight-n6700` | Keysight/Agilent N6700-series mainframe | >=3.10 |
| `rf_ngi_n83624` | `rf-ngi-n83624` | NGI N83624 24-channel cell simulator | >=3.10 |
| `rf_phidget_relay` | `rf-phidget-relay` | Phidget USB relay boards | >=3.9 |
| `rf_votsch_climate_chamber` | `rf-votsch-climate-chamber` | Vötsch/Weiss climate chamber | >=3.11 |

Because `rf_votsch_climate_chamber` needs the newest interpreter, **use Python
3.11 or later** if you want one virtual environment that can install every
package in this repo.

## 1. Prerequisites

- Python 3.11+ (check with `python3 --version`)
- `git` (to have cloned this repository)
- On Linux, membership in the `dialout` group (or equivalent) if you'll talk
  to instruments over a real serial port:
  ```bash
  sudo usermod -aG dialout "$USER"   # log out/in for it to take effect
  ```
- For VISA/GPIB/USBTMC instruments (`rf_bk8500b`, `rf_hp34401a`,
  `rf_keysight_n6700`), a VISA backend — either a vendor implementation
  (NI-VISA, Keysight IO Libraries Suite) or the pure-Python `pyvisa-py`
  backend installed via the extras below.
- For `rf_phidget_relay`, the `Phidget22` Python SDK is installed automatically
  as a normal dependency, but on Linux you may also need udev rules /
  sufficient USB permissions for the relay boards to enumerate — see
  [Phidgets' Linux setup documentation](https://www.phidgets.com/docs/OS_-_Linux)
  if devices aren't found after installing the SDK.

## 2. Create and activate a virtual environment

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 3. Install the packages

Each package is installed as an **editable install** (`-e`) from its own
directory, run from the repository root. Install only the ones you need, or
run all eight.

### Everything, with development/test extras

```bash
python -m pip install -e "./rf_bk8500b[dev]"
python -m pip install -e "./rf_bk8500_load[dev]"
python -m pip install -e "./rf_eresistor[test,yaml]"
python -m pip install -e "./rf_hp34401a[dev,hardware]"
python -m pip install -e "./rf_keysight_n6700[dev,docs]"
python -m pip install -e "./rf_ngi_n83624[dev,docs]"
python -m pip install -e "./rf_phidget_relay[dev]"
python -m pip install -e "./rf_votsch_climate_chamber[dev]"
```

### Minimal runtime install (no dev/test tooling)

```bash
python -m pip install -e ./rf_bk8500b
python -m pip install -e ./rf_bk8500_load
python -m pip install -e ./rf_eresistor
python -m pip install -e ./rf_hp34401a
python -m pip install -e ./rf_keysight_n6700
python -m pip install -e ./rf_ngi_n83624
python -m pip install -e ./rf_phidget_relay
python -m pip install -e ./rf_votsch_climate_chamber
```

All eight distribution names are unique, so they coexist in the same
environment without conflicts.

## 4. Optional hardware-transport extras

Install these only for the packages/transports you'll actually use:

```bash
# VISA/GPIB/USBTMC support without a vendor VISA install (pure Python)
python -m pip install -e "./rf_keysight_n6700[visa-py]"
python -m pip install -e "./rf_bk8500b[visa]"
python -m pip install -e "./rf_hp34401a[hardware]"   # pulls in both pyvisa and pyserial
```

`rf_bk8500_load`, `rf_ngi_n83624`, and `rf_phidget_relay` install their
transport dependencies (`pyserial`, `Phidget22`) unconditionally — no extra
needed.

## 5. Verify the installation

Robot Framework itself:
```bash
python -m robot --version
```

Each package's own test suite (recommended after installing its `dev`/`test`
extra):
```bash
python -m pytest rf_bk8500b/tests -q
python -m pytest rf_bk8500_load/tests -q
python -m pytest rf_eresistor/tests -q
python -m pytest rf_hp34401a/tests -q
python -m pytest rf_keysight_n6700/tests -q
python -m pytest rf_ngi_n83624/tests -q
python -m pytest rf_phidget_relay/tests -q
python -m pytest rf_votsch_climate_chamber/tests -q
```

Import a library from Robot Framework directly to confirm it's on the path:
```bash
python -c "import BK8500BLibrary, bk8500_load, rf_eresistor, rf_hp34401a, KeysightN6700Library, rf_ngi_n83624, rf_phidget_relay, rf_votsch_climate_chamber; print('all imports OK')"
```

## Notes

- Each package also has its own `README.md` with package-specific setup
  detail (example suites, hardware-specific configuration, simulated vs.
  real-device usage) — this file only covers getting the Python
  environment installed.
- None of these libraries touch hardware on import or on Robot Framework
  `Library` load; connecting is always an explicit keyword call
  (`Connect`, `Connect To ...`, `Open ... Connection`, etc.).

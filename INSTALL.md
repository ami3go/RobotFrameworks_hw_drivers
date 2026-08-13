# Installing the RobotFrameworks_hw_drivers packages

This repository contains fourteen independent Robot Framework hardware-instrument
driver packages. Each ships as its own installable Python distribution with
its own `pyproject.toml`, so they can be installed together in one virtual
environment or individually as needed.

| Package | Distribution name | Instrument | Requires Python |
|---|---|---|---|
| `rf_agilent33220a` | `robotframework-agilent33220a` | Agilent 33220A function generator | >=3.10 |
| `rf_agilent34411a` | `robotframework-agilent34411a` | Agilent 34411A DMM | >=3.10 |
| `rf_bk8500b` | `robotframework-bk8500b` | B&K Precision 8500B electronic load | >=3.10 |
| `rf_bk8500_load` | `bk8500-load` | B&K Precision 8500 series DC load | >=3.9 |
| `rf_ea_ps9000t` | `robotframework-ea-ps9000t` | EA-PS 9000 T series power supply | >=3.10 |
| `rf_eresistor` | `rf-eresistor` | OpenBench E-Resistor | >=3.10 |
| `rf_hp34401a` | `rf-hp34401a` | HP/Agilent/Keysight 34401A DMM | >=3.10 |
| `rf_keysight_n6700` | `robotframework-keysight-n6700` | Keysight/Agilent N6700-series mainframe | >=3.10 |
| `rf_ngi_n83624` | `rf-ngi-n83624` | NGI N83624 24-channel cell simulator | >=3.10 |
| `rf_phidget_relay` | `rf-phidget-relay` | Phidget USB relay boards | >=3.9 |
| `rf_picoscope2000a` | `robotframework-picoscope2000a` | PicoScope 2000A-family oscilloscope + AWG | >=3.10 |
| `rf_slcan` | `robotframework-slcan` | SLCAN-compatible CAN adapters | >=3.10 |
| `rf_tbs1000c` | `robotframework-tbs1000c` | Tektronix TBS1000C oscilloscope | >=3.10 |
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
- For VISA/GPIB/USBTMC instruments (`rf_agilent33220a`, `rf_agilent34411a`,
  `rf_bk8500b`, `rf_ea_ps9000t`, `rf_hp34401a`, `rf_keysight_n6700`,
  `rf_tbs1000c`), a VISA backend — either a vendor implementation (NI-VISA,
  Keysight IO Libraries Suite) or the pure-Python `pyvisa-py` backend
  installed via the extras below.
- For `rf_phidget_relay`, the `Phidget22` Python SDK is installed automatically
  as a normal dependency, but on Linux you may also need udev rules /
  sufficient USB permissions for the relay boards to enumerate — see
  [Phidgets' Linux setup documentation](https://www.phidgets.com/docs/OS_-_Linux)
  if devices aren't found after installing the SDK.
- For `rf_picoscope2000a` real hardware, install the `hardware` extra
  (`picosdk`) **and** Pico Technology's own native PicoSDK driver package
  separately — `picosdk` is a ctypes wrapper around it, not a self-contained
  driver. Not needed to run the package's own tests, which use a bundled
  simulator.

## 2. One-command install (recommended)

Run the installer from the repository root. It creates a virtual environment
(`.venv` by default) and installs all fourteen packages as editable installs
into it.

macOS/Linux:
```bash
./install.sh            # runtime-only installs
./install.sh --dev       # also install each package's dev/test/docs extras
```

Windows (PowerShell):
```powershell
.\install.ps1            # runtime-only installs
.\install.ps1 -Dev        # also install each package's dev/test/docs extras
```

Useful flags (both scripts support the equivalent options):

| Bash | PowerShell | Purpose |
|---|---|---|
| `--dev` | `-Dev` | Add each package's dev/test/docs extras |
| `--no-venv` | `-NoVenv` | Install into the currently active Python env instead of creating one |
| `--venv PATH` | `-VenvDir PATH` | Use a venv at a custom path (default: `.venv`) |
| `--python PY` | `-Python PY` | Python executable to use (default: `python3` / `python`) |

Activate the environment afterwards:
```bash
source .venv/bin/activate            # macOS/Linux
.\.venv\Scripts\Activate.ps1         # Windows
```

The rest of this document explains what the installer does manually, and how
to install packages individually, in case you don't want to use it.

## 3. Create and activate a virtual environment manually

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

## 4. Install the packages manually

Each package is installed as an **editable install** (`-e`) from its own
directory, run from the repository root. Install only the ones you need, or
run all fourteen.

### Everything, with development/test extras

```bash
python -m pip install -e "./rf_agilent33220a[dev]"
python -m pip install -e "./rf_agilent34411a[dev]"
python -m pip install -e "./rf_bk8500b[dev]"
python -m pip install -e "./rf_bk8500_load[dev]"
python -m pip install -e "./rf_ea_ps9000t[dev]"
python -m pip install -e "./rf_eresistor[test,yaml]"
python -m pip install -e "./rf_hp34401a[dev,hardware]"
python -m pip install -e "./rf_keysight_n6700[dev,docs]"
python -m pip install -e "./rf_ngi_n83624[dev,docs]"
python -m pip install -e "./rf_phidget_relay[dev]"
python -m pip install -e "./rf_picoscope2000a[dev]"
python -m pip install -e "./rf_slcan[dev]"
python -m pip install -e "./rf_tbs1000c[dev]"
python -m pip install -e "./rf_votsch_climate_chamber[dev,docs]"
```

### Minimal runtime install (no dev/test tooling)

```bash
python -m pip install -e ./rf_agilent33220a
python -m pip install -e ./rf_agilent34411a
python -m pip install -e ./rf_bk8500b
python -m pip install -e ./rf_bk8500_load
python -m pip install -e ./rf_ea_ps9000t
python -m pip install -e ./rf_eresistor
python -m pip install -e ./rf_hp34401a
python -m pip install -e ./rf_keysight_n6700
python -m pip install -e ./rf_ngi_n83624
python -m pip install -e ./rf_phidget_relay
python -m pip install -e ./rf_picoscope2000a
python -m pip install -e ./rf_slcan
python -m pip install -e ./rf_tbs1000c
python -m pip install -e ./rf_votsch_climate_chamber
```

All fourteen distribution names are unique, so they coexist in the same
environment without conflicts.

## 5. Optional hardware-transport extras

Install these only for the packages/transports you'll actually use:

```bash
# VISA/GPIB/USBTMC support without a vendor VISA install (pure Python)
python -m pip install -e "./rf_agilent33220a[visa-py]"
python -m pip install -e "./rf_agilent34411a[visa-py]"
python -m pip install -e "./rf_ea_ps9000t[visa-py]"
python -m pip install -e "./rf_keysight_n6700[visa-py]"
python -m pip install -e "./rf_bk8500b[visa]"
python -m pip install -e "./rf_hp34401a[hardware]"   # pulls in both pyvisa and pyserial
python -m pip install -e "./rf_slcan[serial]"
python -m pip install -e "./rf_tbs1000c[usbtmc]"

# PicoScope 2000A-family: real hardware (native PicoSDK driver required too, see above)
python -m pip install -e "./rf_picoscope2000a[hardware]"
# PicoScope 2000A-family: image export (Save Channel Image / Save All Channels Image)
python -m pip install -e "./rf_picoscope2000a[plot]"
```

`rf_bk8500_load`, `rf_ngi_n83624`, and `rf_phidget_relay` install their
transport dependencies (`pyserial`, `Phidget22`) unconditionally — no extra
needed.

## 6. Verify the installation

Robot Framework itself:
```bash
python -m robot --version
```

Each package's own test suite (recommended after installing its `dev`/`test`
extra):
```bash
python -m pytest rf_agilent33220a/tests -q
python -m pytest rf_agilent34411a/tests -q
python -m pytest rf_bk8500b/tests -q
python -m pytest rf_bk8500_load/tests -q
python -m pytest rf_ea_ps9000t/tests -q
python -m pytest rf_eresistor/tests -q
python -m pytest rf_hp34401a/tests -q
python -m pytest rf_keysight_n6700/tests -q
python -m pytest rf_ngi_n83624/tests -q
python -m pytest rf_phidget_relay/tests -q
python -m pytest rf_picoscope2000a/tests -q
python -m pytest rf_slcan/tests -q
python -m pytest rf_tbs1000c/tests -q
python -m pytest rf_votsch_climate_chamber/tests -q
```

Import a library from Robot Framework directly to confirm it's on the path:
```bash
python -c "import rf_agilent33220a, rf_agilent34411a, BK8500BLibrary, bk8500_load, rf_ea_ps9000t, rf_eresistor, rf_hp34401a, KeysightN6700Library, rf_ngi_n83624, rf_phidget_relay, rf_picoscope2000a, rf_slcan, rf_tbs1000c, rf_votsch_climate_chamber; print('all imports OK')"
```

## Notes

- Each package also has its own `README.md` with package-specific setup
  detail (example suites, hardware-specific configuration, simulated vs.
  real-device usage) — this file only covers getting the Python
  environment installed.
- None of these libraries touch hardware on import or on Robot Framework
  `Library` load; connecting is always an explicit keyword call
  (`Connect`, `Connect To ...`, `Open ... Connection`, etc.).

# rf_keysight349xx

Robot Framework driver for the **Keysight/Agilent 34970A and Keysight 34972A**.

## Current status

**Release: `26.1.0` / archive `rf_keysight349xx_v26.1.zip`**  
**Release class: D0 — Phase 1 / Gate 2 foundation.**

Implemented now:

- the ten RFDS-002 v1.1 universal keywords;
- multi-connection group;
- strict `*IDN?` identity parsing for 34970A/34972A;
- `SYST:CTYP?` module discovery for slots 100/200/300;
- `SYST:VERS?` SCPI-version query;
- complete RFDS `error_queue` keyword group using `SYST:ERR?` and `*CLS`;
- byte-oriented transport boundary;
- strict stateful simulator;
- optional PyVISA backend;
- protocol trace records with operation identifiers;
- public API/AI contract/conformance-vector skeleton;
- 11 simulator-runnable Robot examples;
- 29 passing software unit tests and package validation scripts.

Not yet claimed:

- measurement, scan, switching, temperature, 34907A digital/totalizer/DAC, or 34972A file/LAN configuration groups;
- full RFDS-019 execution evidence;
- real 34970A/34972A HIL evidence;
- D1/D2/P1 readiness.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

For VISA hardware:

```bash
python -m pip install -e '.[visa]'
```

## Robot Framework example

```robotframework
*** Settings ***
Library    rf_keysight349xx.library.Keysight349xxLibrary
Suite Teardown    Disconnect All

*** Test Cases ***
Read Identity And Modules
    ${state}=    Connect    SIM::34972A    alias=daq
    Should Be True    ${state}[connected]
    ${idn}=    Get Identity    alias=daq
    Log    ${idn}
    ${modules}=    Get Installed Modules    alias=daq
    Log Many    @{modules}
```

Run all examples:

```bash
./scripts/run_all_examples.sh
```

## Hardware resources

D0 accepts simulator resources such as `SIM::34972A` and VISA resource strings such as a configured GPIB/USB/LAN VISA endpoint. No hardware connection is opened during package import or library construction.

## Important D0 deviation

RFDS-003 v2.0 requires a shared `rfds-core` distribution. The current project repository does not contain that shared component, so this D0 package uses a small compatibility `BaseInstrumentLibrary` under deviation `DEV-RFDSCORE-001`. It must be replaced and the shared contract suite passed before D1.

## Source authority

Protocol behavior in this implementation slice is based on the supplied Keysight/Agilent 34970A/34972A Command Reference. Calibration/security commands are intentionally not exposed.

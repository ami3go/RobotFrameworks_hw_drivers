# RFDS Vötsch Climate Chamber Driver

Release **v26.09** (`26.9` in Python metadata) adds an RFDS-008 live evidence engine on top of the v26.08 real-chamber hardening.

> Release class: **D0 / D1 candidate**. Python, simulator, metadata, packaging, and clean-install gates are automated. Native Robot RFDS-019 execution and representative real-device qualification remain required before D1/D2/P1 acceptance.

## What changed in v26.09

- Added a live RFDS-008 evidence engine (`evidence.py`): every keyword call and every SimServ protocol frame (via the existing `TraceObserver` mechanism) is recorded to a correlated, SHA-256-integrity-checked run under `results/session/rf_votsch_climate_chamber/`. See [Evidence and diagnostics](docs/TROUBLESHOOTING.md#evidence-and-diagnostics-which-one-do-i-want) for how this differs from the pre-existing `Get/Export Diagnostics` snapshot.
- Added the `Export Diagnostic Bundle` keyword (58th canonical keyword).
- Added `scripts/validate_evidence.py` (+ `.sh`/`.bat`/`.ps1`) to verify a run's integrity offline.

## What changed in v26.08

- setpoint writes now use bounded polling because real hardware can acknowledge before readback changes;
- effective configuration is round-trippable, so close-only hardware teardown is actually applied;
- `Safe Shutdown` stops the chamber but skips dryer/compressed-air/fan commands until physical channels are explicitly qualified;
- hardware suites verify configuration application and gate auxiliary I/O by authorization and mapping;
- targeted regression tests cover the two reported hardware failures.

API 2 aliases remain removed as documented in [`docs/migration.md`](docs/migration.md).

## Architecture and safety

- explicit Robot keyword export (`auto_keywords=False`);
- suite-scoped, named connection sessions;
- TCP and deterministic simulator transports;
- finite timeouts, bounded cleanup, cancellation, readback verification, and
  configured temperature limits;
- RFDS-007 typed errors with stable codes and recovery guidance;
- RFDS-014 configuration profiles;
- RFDS-015 plugin descriptor and `rfds.drivers` entry point;
- RFDS-017 AI contract and RFDS-019 protocol vectors;
- fixed release root `rf_votsch_climate_chamber/`.

## Installation

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

Linux:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
```

## First Robot test

```robotframework
*** Settings ***
Library    rf_votsch_climate_chamber.VotschClimateChamberLibrary
Suite Teardown    Disconnect All

*** Test Cases ***
Read Simulator Temperature
    ${state}=    Connect    resource=SIM::default    alias=default
    Should Be True    ${state}[connected]
    ${temperature}=    Measure Temperature
    Log    ${temperature} °C
```

Run:

```powershell
python -m robot --outputdir results/quickstart quick_start.robot
```

## Real chamber connection

```robotframework
Connect
...    resource=tcp://192.168.0.50:2049
...    alias=default
...    timeout_s=5 seconds
...    temperature_min_c=-40
...    temperature_max_c=180
```

Use named arguments for `Connect`. Real hardware defaults to no dryer, compressed-air or fan mapping. Supply `dryer_output_channel`, `compressed_air_output_channel` or `fan_output_channel` only after qualification.

## Validation

```powershell
python scripts/generate_rfds_metadata.py
python scripts/validate_structure.py
python scripts/validate_ai_contract.py
python scripts/validate_call_protocol_conformance.py
python scripts/run_python_simulator_smoke.py
python -m pytest --cov=rf_votsch_climate_chamber --cov-branch
```

When Robot Framework is installed:

```powershell
python scripts/run_conformance.py
python scripts/run_all_examples.py --dry-run
```

Validate the integrity of an evidence run produced by any of the above (or by real hardware):

```console
python scripts/validate_evidence.py results/session/rf_votsch_climate_chamber/<run>/
```

## Hardware tests

`tests/hardware/verify_all_api.robot` (RFDS-019-hil, real chamber required) and `tests/hardware/smoke_test.robot` cover the real-hardware surface; `tests/conformance/driver_call_protocol_conformance.robot` covers RFDS-019 protocol conformance against the simulator. Run against a real chamber:

```console
python -m robot --outputdir results -v CHAMBER_IP:192.168.0.50 tests/hardware/verify_all_api.robot
```

State-changing profiles (`ALLOW_CHAMBER_CONTROL`, `ALLOW_AUXILIARY_OUTPUTS`) default to `${FALSE}` — see the suite's own `Documentation` and `docs/safety.md` before enabling either.

## Documentation

- [Installation](docs/installation.md)
- [Quick start](docs/quick_start.md)
- [Canonical keyword reference](docs/keywords.md)
- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [API 3.0 migration](docs/migration.md)
- [Safety](docs/safety.md)
- [RFDS-019 conformance](docs/call_protocol_conformance.md)
- [Release notes](docs/release_notes.md)
- [Changed-file review](review/v26.08_file_by_file_review.md)
- [Known risks](review/known_risks.md)

## Package identity

```text
rf_votsch_climate_chamber_v26.08.zip
└── rf_votsch_climate_chamber/
```

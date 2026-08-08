# RF HP34401A

Robot Framework driver for the HP/Agilent/Keysight 34401A 6½-digit DMM.

| Item | Value |
|---|---|
| Release | **26.07** |
| Python distribution | `rf-hp34401a` 26.7.0 |
| Core driver | `hp34401a_dmm` 1.2.8 |
| Release class | **D0 — development candidate** |
| Python | 3.10–3.13 |
| Robot Framework | 7.x |
| Public Robot keywords | 109 |
| RFDS baseline | RFDS-001 v1.2, RFDS-002 v1.1, RFDS-003 v2.0, RFDS-004 v2.0, RFDS-005 v1.3, RFDS-007 v1.0, RFDS-009 v1.0, RFDS-013 v1.0, RFDS-014 v1.0, RFDS-015 v1.0, RFDS-017 v3.0, RFDS-018 v1.0, RFDS-019 v1.1 |

The public Robot adapter delegates SCPI behavior to the reviewed `hp34401a_dmm` core. It rejects overload, invalid, missing, and unstable readings instead of returning plausible fabricated values. Hardware connection never silently falls back to simulation.

## Install with uv

From the extracted folder containing `pyproject.toml`:

```powershell
uv pip install -e ".[hardware]"
```

Development and validation dependencies:

```powershell
uv pip install -e ".[dev,hardware]"
```

A vendor VISA implementation such as Keysight IO Libraries Suite or NI-VISA is required for real VISA/GPIB/USBTMC access.

## Canonical quick start

```robotframework
*** Settings ***
Library           rf_hp34401a.Hp34401ALibrary
Suite Teardown    Disconnect All

*** Test Cases ***
Measure A Real DC Voltage
    ${state}=    Connect
    ...    resource=GPIB0::22::INSTR
    ...    alias=dmm
    ...    timeout_s=10 s
    ...    transport=VISA
    Should Be True    ${state}[connected]

    ${identity}=    Get Identity    alias=dmm
    Log    ${identity}

    ${voltage}=    Measure DC Voltage
    ...    range_value=100
    ...    nplc=10
    ...    alias=dmm
    DMM Reading Should Be Between    11.5    12.5    alias=dmm
```

The RFDS-002 canonical lifecycle is:

- `Connect`
- `Disconnect`
- `Is Connected`
- `Get Connection State`
- `Check Communication`
- `Get Identity`
- `Get Driver Information`
- `Get Driver Capabilities`
- `Set Communication Timeout`
- `Get Communication Timeout`

The older DMM-specific names remain available for compatibility, including `Connect DMM`, `Open DMM Via VISA`, `Open DMM Via Serial`, `Close DMM`, `Identify DMM`, and the complete measurement API.

## Capability and configuration discovery

RFDS-013 discovery:

```robotframework
${ids}=      Get Driver Capabilities
${model}=    Get Driver Capability Model    mode=static
${matches}=  Find Driver Capabilities    capability_id=measure.    maximum_risk=low
```

RFDS-014 JSON configuration:

```robotframework
${default}=      Get Driver Default Configuration
${validation}=   Validate Driver Configuration    ${default}
${effective}=    Import Driver Configuration      ${default}
${json}=         Export Driver Configuration
```

Configuration import never opens hardware or writes device non-volatile state. Persistence occurs only through `Save Driver Configuration`.

## RFDS-019 protocol conformance

The package contains a 109-keyword inventory and protocol-vector set under `tests/conformance/`.

```powershell
python scripts/validate_ai_contract.py
python scripts/validate_call_protocol_conformance.py
.\scripts\run_call_protocol_conformance.ps1
```

Simulation conformance is distinct from physical hardware evidence.

## Verify every public API on real hardware

The explicitly enabled suite is:

```text
tests/hil/verify_all_public_api_real_hardware.robot
```

Run the read-only/default profile:

```powershell
.\scripts\run_all_api_hil.ps1 `
    -VisaResource "GPIB0::22::INSTR"
```

The suite inventories all 109 public keywords and gives every one a visible `PASS`, `FAIL`, `EXCLUDED`, or `NOT RUN` result. Measurement, trigger, reset, self-test, raw-I/O, and serial profiles are disabled until their corresponding fixture and authorization variables are explicitly supplied. Use `-FailOnExclusions` for a zero-exclusion qualification run.

Example enabling a verified DC-voltage fixture:

```powershell
.\scripts\run_all_api_hil.ps1 `
    -VisaResource "GPIB0::22::INSTR" `
    -ExtraRobotArgs @(
        "--variable", "RUN_DC_VOLTAGE_PROFILE:True"
    )
```

The suite produces Robot `output.xml`, `log.html`, and `report.html` plus JSON, CSV, Markdown, environment, and per-keyword coverage evidence in a timestamped result directory. It never falls back to simulation after a real-hardware connection failure.

## Logging and evidence

Every public keyword call is recorded as RFDS-008 structured evidence — arguments, duration,
result/failure, and the literal SCPI commands/responses it caused on whichever transport
(VISA, RS-232, or the simulator) carried it — under `results/session/rf_hp34401a/<run>/`
(override with `RFDS_EVIDENCE_ROOT`). This is a per-session diagnostic layer distinct from
`logging_utils.py`'s production CSV/JSONL measurement logs, and from the coverage bookkeeping
in `tests/hil/`/`tests/conformance/` above; see
[Logging and Evidence](docs/logging_and_evidence.md) and
[guide/evidence_and_diagnostics.md](guide/evidence_and_diagnostics.md) for what gets recorded
and how to read it after a failure.

```robotframework
Library    rf_hp34401a.Hp34401ALibrary    evidence_enabled=${FALSE}    # disables it; on by default
```

Call the `Export Diagnostic Bundle` keyword to zip the current run for a bug report. Validate a
run's integrity (hashes, JSONL sequencing) with:

```console
python scripts/validate_evidence.py results/session/rf_hp34401a/<run>/
```

## Safety

- Verify the selected front/rear input terminal before energizing the fixture.
- Current tests require the correct fused current terminal and an approved bounded source.
- Resistance, continuity, and diode tests require a verified de-energized DUT.
- Reset and self-test can disturb a production setup and require explicit profile enablement.
- Raw SCPI is disabled by default and must be enabled explicitly.
- The included RFDS-018 file is a template, not a claim about your actual bench wiring or limits.

## Validation status

Validation for this hotfix:

- the inherited core suite passes with 67 software tests and 2 explicitly guarded physical tests skipped;
- Python compilation passed after the HIL evidence-state correction;
- a file-backed listener regression proved that executed PASS results override prior EXCLUDED records and that no keyword remains NOT RUN when all unexecuted APIs have approved exclusions;
- RFDS-002/RFDS-017 synchronization passed for 109 keywords;
- RFDS-019 static inventory/vector validation passed for 109 keywords;
- the real-hardware suite accounts for all 109 public keyword names;
- the user's v26.05 physical run proved VISA discovery, real HP34401A connection, identity, health/error/recovery, simulation isolation, and cleanup, and exposed only the now-corrected evidence bookkeeping defect.

Robot Framework is not installed in the package-build container. Rerun the v26.06 packaged launcher in the release-site uv environment to generate corrected Robot and physical-device evidence before promotion to D2 or P1. The package does not claim D2/P1 hardware qualification.

## Project contents

- `rf_hp34401a/` — explicit Robot adapter and RFDS metadata services;
- `hp34401a_dmm/` — device core and existing VISA/serial/fake transports;
- `api/` — RFDS-002 API inventory and decisions;
- `capability/` — RFDS-013 capability model;
- `config/` — RFDS-014 schema, safe defaults, and examples;
- `ai/` — RFDS-017 contract and lock;
- `tests/conformance/` — RFDS-019 inventory, vectors, runners, and schemas;
- `tests/hil/` — opt-in real-device tests, including all-public-API verification;
- `examples/` — 13 numbered Robot examples;
- `history/`, `review/`, `release/` — change, review, risk, traceability, and integrity records;
- `guide/`, `docs/`, `mkdocs.yml` — setup and GitHub Pages sources.

## License

MIT. The incorporated core retains its original MIT licensing and attribution.

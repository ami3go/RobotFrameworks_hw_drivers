# RF HP34401A

Robot Framework driver for the HP/Agilent/Keysight 34401A 6½-digit DMM.

| Item | Value |
|---|---|
| Last released API baseline | **26.07** / distribution `26.7.0` |
| Current branch state | **Unreleased remediation candidate** |
| Core driver | `hp34401a_dmm` 1.2.8 plus RFDS runtime-policy facade |
| Release class | **D0 — development candidate** |
| Python | 3.10–3.13 |
| Robot Framework | 7.x |
| Public Robot keywords | 109 |
| Runtime dependencies | `robotframework>=7,<8`, `rfds-core>=1.0,<2.0`, `jsonschema>=4.20,<5` |
| Remaining RFDS-003 blocker | authoritative `BaseInstrumentLibrary` integration |
| Hardware qualification | **PENDING on exact corrected commit** |

The public Robot adapter delegates SCPI measurement behavior to the reviewed `hp34401a_dmm` core. It rejects overload, invalid, missing, and unstable readings instead of returning plausible fabricated values. Hardware connection never silently falls back to simulation.

## Current remediation status

The 2026-08-16 deep review found cross-file and release-governance defects that were not visible in the earlier high-level review. The `dev` branch now includes corrections for:

- repository-root GitHub Actions CI/HIL/Pages workflows;
- fail-closed RFDS-008 evidence run status and manifest-stable diagnostic export;
- listener cleanup evidence finalization and correct simulation/real-hardware evidence mode;
- Draft 2020-12 RFDS-014 schema validation and structured schema-lock verification;
- effective runtime application of imported timeout/retry/safety/logging/simulation/device settings;
- finite-positive communication timeout enforcement;
- structured public validation errors;
- RFDS-013 capability/runtime-model synchronization and real Robot export validation;
- mandatory `rfds-core` version checking/reporting;
- installed-wheel plugin artifact resolution;
- version-derived release building, stale-release-evidence invalidation, and removal of committed generated MkDocs `site/` output;
- the missing v26.07 retrospective code-review record.

The package **does not yet claim full RFDS-003 conformance**. The connected repository/environment does not provide the authoritative shared `rfds-core` implementation needed to integrate `BaseInstrumentLibrary` safely. A local compatibility copy is intentionally not created.

## Install

From the extracted driver directory containing `pyproject.toml`:

```powershell
uv pip install -e ".[hardware]"
```

or:

```bash
python -m pip install -e ".[hardware]"
```

An approved `rfds-core>=1.0,<2.0` distribution must be available to the package installer. Real VISA/GPIB access additionally requires a VISA implementation such as Keysight IO Libraries Suite or NI-VISA.

Development environment:

```powershell
uv pip install -e ".[dev,hardware]"
```

## Canonical RFDS-002 lifecycle

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
    Should Be True    ${state}[communication_ok]

    ${identity}=    Get Identity    alias=dmm
    Log    ${identity}

    ${voltage}=    Measure DC Voltage
    ...    range_value=100
    ...    nplc=10
    ...    alias=dmm
    DMM Reading Should Be Between    11.5    12.5    alias=dmm
```

The ten universal keywords are:

1. `Connect`
2. `Disconnect`
3. `Is Connected`
4. `Get Connection State`
5. `Check Communication`
6. `Get Identity`
7. `Get Driver Information`
8. `Get Driver Capabilities`
9. `Set Communication Timeout`
10. `Get Communication Timeout`

Compatibility names such as `Connect DMM`, `Open DMM Via VISA`, `Open DMM Via Serial`, `Close DMM`, and `Identify DMM` remain available.

### `verify_identity` semantics

`verify_identity=False` disables the model-validation step performed during transport connection. Canonical `Connect` still performs the bounded RFDS-002 communication probe required to populate `communication_ok`; therefore it may still issue a safe `*IDN?` probe before returning.

## RFDS-014 configuration

Configuration import is host-side only and does not open hardware or write instrument non-volatile state.

```robotframework
${default}=       Get Driver Default Configuration
${validation}=    Validate Driver Configuration    ${default}
${effective}=     Import Driver Configuration      ${default}
${json}=          Export Driver Configuration
```

Configuration is validated against `config/schema.json`; the schema SHA-256 is verified against the structured `config/schema.lock` before a `ConfigurationManager` is created.

A validated imported profile can control:

- transport resource and transport kind;
- communication, self-test and long-measurement timeouts;
- safe query retry policy;
- raw traffic logging;
- explicit simulation selection and deterministic reading/identity;
- raw-SCPI and calibration authorization;
- expected model/terminal policy.

Package-default simulation is disabled. An omitted resource can select simulation only when a validated imported profile explicitly sets `settings.simulation.enabled=true`; a failed or missing real hardware resource is never replaced by simulation.

## RFDS-013 capabilities

```robotframework
${ids}=      Get Driver Capabilities
${model}=    Get Driver Capability Model    mode=static
${matches}=  Find Driver Capabilities    capability_id=measure.    maximum_risk=low
```

Capability binding validation compares the RFDS model to the actual decorated Robot export surface rather than validating the model against itself.

## Logging and evidence

Every public keyword call is recorded as RFDS-008 structured evidence under:

```text
results/session/rf_hp34401a/<run>/
```

The evidence engine records operation arguments/results/failures, identity/environment information, and correlated SCPI protocol traffic. Important fail-closed behavior:

- any failed operation keeps the final run status at `FAIL` even if later cleanup succeeds;
- simulation is labeled `SIMULATION`, not real hardware;
- listener cleanup finalizes the run if an explicit disconnect was omitted;
- diagnostic bundle export writes the export event before hashing the snapshot, so the live manifest remains valid.

Disable evidence explicitly only when required:

```robotframework
Library    rf_hp34401a.Hp34401ALibrary    evidence_enabled=${FALSE}
```

Validate evidence:

```console
python scripts/validate_evidence.py results/session/rf_hp34401a/<run>/
```

## RFDS-019 and HIL

Static call/protocol validation:

```powershell
python scripts/validate_ai_contract.py
python scripts/validate_call_protocol_conformance.py
.\scripts\run_call_protocol_conformance.ps1
```

Real-hardware all-public-API verification:

```powershell
.\scripts\run_all_api_hil.ps1 -VisaResource "GPIB0::22::INSTR"
```

The HIL suite inventories all 109 public keywords and requires explicit fixture/authorization profiles for operations that can disturb the DUT or instrument. Simulation evidence is never accepted as a substitute for D2/P1 physical evidence.

## CI and GitHub Pages

Active repository-root workflows are:

```text
.github/workflows/rf_hp34401a-ci.yml
.github/workflows/rf_hp34401a-hil.yml
.github/workflows/rf_hp34401a-pages.yml
```

The quality workflow runs on Windows/Linux and Python 3.10/3.13, performs static contract checks, Python/Robot tests, >=80% combined adapter+core coverage, offline examples, Libdoc, strict MkDocs build, wheel/sdist build, and installed-wheel plugin-resource validation. It finishes with an explicit shared-core release gate, so release qualification remains blocked when the authoritative `rfds-core` is unavailable.

GitHub Pages builds `site/` from `docs/` and `mkdocs.yml`; generated `site/` output is not tracked in Git.

## Release packaging

`scripts/build_release.py` derives release/distribution versions from the package authorities. It refuses to package a current release when required history/review records are missing and regenerates provenance/checksums from the frozen source commit.

Current `release/` files are deliberately marked as remediation/pending where evidence has not been regenerated. Do not treat them as a production release attestation until CI and real HIL have completed on the exact frozen commit.

## Safety

- Verify the selected front/rear input terminal before energizing the fixture.
- Current tests require the correct fused current terminal and an approved bounded source.
- Resistance, continuity and diode tests require a verified de-energized DUT.
- Reset and self-test can disturb a production setup and require explicit authorization/profile enablement.
- Raw SCPI is disabled by package default and must be explicitly enabled by constructor, keyword, or validated safety profile.
- Calibration commands are separately guarded.
- The RFDS-018 bench file is a template, not a claim about actual bench wiring or limits.

## Project contents

- `rf_hp34401a/` — active Robot facade, plugin, RFDS metadata/configuration services;
- `rf_hp34401a/legacy_library.py` — preserved reviewed 26.07 keyword implementation under the corrected facade;
- `hp34401a_dmm/` — active core facade and transport/measurement implementation;
- `hp34401a_dmm/legacy_driver.py` — preserved reviewed 1.2.8 core implementation;
- `api/` — RFDS-002 API inventory, compatibility, decisions and deviations;
- `capability/` — RFDS-013 capability model;
- `config/` — RFDS-014 schema, lock, defaults and examples;
- `ai/` — RFDS-017 contract and lock;
- `tests/conformance/` — RFDS-019 inventory/vectors/runners;
- `tests/hil/` — opt-in real-device verification;
- `examples/` — 13 numbered Robot examples;
- `history/`, `review/`, `release/` — lifecycle/change/review/integrity records;
- `guide/`, `docs/`, `mkdocs.yml` — setup and GitHub Pages sources.

## License

MIT. The incorporated core retains its original MIT licensing and attribution.

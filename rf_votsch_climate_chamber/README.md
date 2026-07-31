# Robot Framework Vötsch Climate Chamber Library

**Release:** v26.02  
**Python package version:** 26.2  
**Status:** production-oriented release candidate; real-chamber validation is still required for each chamber model and site configuration.

This repository contains two deliberately separate layers:

```text
Robot Framework tests
        │ readable, safety-focused keywords
        ▼
VotschClimateChamberLibrary
        │ composition, not inheritance
        ▼
ClimateChamber Python driver
        │ reconnecting TCP protocol, validation, readback
        ▼
Vötsch / SimServ-compatible chamber, TCP port 2049
```

## Why an adapter instead of modifying the driver into Robot keywords?

The driver remains useful from Python, pytest, CLI tools, and other automation systems. The Robot adapter adds suite lifecycle, Robot time syntax, explicit keyword exposure, logging, assertions, and safe teardown without mixing framework concerns into the protocol layer.

## Installation

```bash
python -m venv .venv
# Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

## First test

```robot
*** Settings ***
Library         votsch_climate_chamber.robot_library.VotschClimateChamberLibrary
Suite Setup     Connect Climate Chamber    192.168.1.50    -40    180
Suite Teardown  Stop And Disconnect Climate Chamber

*** Test Cases ***
Run At Ambient
    Set Temperature And Wait
    ...    target=25
    ...    tolerance=0.8
    ...    stable_samples=3
    ...    timeout=2 h
    Climate Chamber Temperature Should Be    25    tolerance=0.8
```

Run it with:

```bash
robot --outputdir results my_test.robot
```

## Safety defaults

- Library import never connects to hardware.
- Local minimum and maximum temperatures are mandatory when connecting.
- Out-of-range setpoints fail; they are never silently clamped.
- Waiting keywords use finite default timeouts.
- Raw protocol commands are not exposed as Robot keywords.
- Stopping on ordinary disconnect is configurable.
- `Stop And Disconnect Climate Chamber` always attempts both operations.
- Real-hardware tests are opt-in.

A host process cannot guarantee safe chamber behavior after host power loss, network failure, relay failure, or chamber-controller malfunction. Configure independent chamber alarms and hardware limits.

## Repository layout

Release archives follow the shared driver convention: `rf_votsch_climate_chamber_vYY.RR.zip`. The extracted project folder is always named `rf_votsch_climate_chamber`, without a version. A later release can therefore replace the existing project folder after local changes are committed or backed up.

```text
rf_votsch_climate_chamber/
├── votsch_climate_chamber/    Python driver and Robot adapter
├── history/                   Versioned change descriptions
├── review/                    Versioned code and requirements reviews
├── examples/                  13 Robot examples
├── scripts/                   Example, validation, test, and release scripts
├── guide/                     PyCharm, Robot Framework, and hardware guides
├── docs/                      Markdown documentation and GitHub Pages source
├── tests/                     Unit, acceptance, simulator, hardware smoke
└── .github/workflows/         CI and GitHub Pages pipelines
```

## Documentation

- [Project requirements](PROJECT_REQUIREMENTS.md)
- [Setup guides](guide/README.md)
- [Release history](history/v26.02.md)
- [Code review](review/v26.02_code_review.md)
- [Keyword reference](docs/KEYWORDS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Safety guide](docs/SAFETY.md)
- [Testing guide](docs/TESTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Driver review](docs/DRIVER_REVIEW.md)
- [Production task and acceptance criteria](docs/IMPLEMENTATION_TASK_v26.01.md)
- [Production-readiness score](docs/PRODUCTION_READINESS_REVIEW.md)
- [Validation report](docs/VALIDATION_REPORT_v26.02.md)
- [Release notes](docs/RELEASE_NOTES_v26.02.md)

## AI-readable contracts

Release v26.02 adds a canonical [RFDS-017 driver contract](ai/ai_contract.yaml), its [staleness lock](ai/ai_contract.lock), and an [RFDS-018 bench template](system_ai_contract.yaml). The driver contract covers all 36 public keywords. The bench template retains explicit `UNKNOWN` values for site-specific chamber, DUT, fixture, reference sensor and emergency procedures, and denies control-changing automation until those values are resolved.

Validate the contracts with:

```bash
python scripts/validate_ai_contract.py
```

See [Using the AI Contracts](guide/AI_CONTRACT_USAGE.md).

## Examples

The `examples/` directory contains 13 complete suites covering lifecycle, limits, stabilization, cycling, gradients, auxiliary outputs, diagnostics, reconnect, assertions, external variable files, and failure-safe teardown.

List or run examples with the cross-platform runner:

```bash
python scripts/run_example.py --list
python scripts/run_example.py 1 --dryrun
```

Windows users can also call `scripts\run_example.bat` or `scripts\run_example.ps1`. Linux users can call `scripts/run_example.sh`.

## Verification commands

```bash
python scripts/validate_project_layout.py
python scripts/validate_ai_contract.py
pytest
robot --pythonpath . --outputdir results tests/robot
python -m robot.libdoc votsch_climate_chamber.robot_library.VotschClimateChamberLibrary docs/VotschClimateChamberLibrary.html
python -m build
python -m twine check dist/*
python -m mkdocs build --strict
python scripts/build_release.py
```

## Release package format

```text
rf_votsch_climate_chamber_v26.02.zip
└── rf_votsch_climate_chamber/
```

The ZIP name changes with each release. The internal folder remains fixed. The release builder and layout validator enforce this rule.

## Versioning

Human release tags use `vYY.RR`: `v26.01`, `v26.02`, and so on. Python package metadata uses the PEP 440 normalized equivalent: `26.1`, `26.2`.

## License

MIT. See [LICENSE](LICENSE).

# Testing Guide

## Test layers

1. `tests/unit/test_driver.py`: protocol helpers, safety, reconnect, driver round trip.
2. `tests/unit/test_robot_library.py`: import behavior, conversion, keyword exposure, lifecycle, assertions.
3. `tests/robot/`: Robot acceptance tests against a local TCP simulator.
4. `tests/hardware/`: opt-in real-chamber smoke tests.

## Local commands

```bash
python -m pip install -e ".[dev]"
pytest --cov=votsch_climate_chamber --cov-report=term-missing
robot --pythonpath . --outputdir results tests/robot
python -m robot.libdoc votsch_climate_chamber.robot_library.VotschClimateChamberLibrary docs/VotschClimateChamberLibrary.html
python -m build
python -m twine check dist/*
```

## Hardware smoke test

Read-only:

```bash
robot --pythonpath . --outputdir results-hardware tests/hardware/smoke_test.robot
```

Operator-approved control:

```bash
robot --pythonpath . --outputdir results-hardware \
  --variable CHAMBER_IP:192.168.1.50 \
  --variable ALLOW_CHAMBER_CONTROL:True \
  tests/hardware/smoke_test.robot
```

Before control-changing tests, confirm safe target, empty/appropriate chamber load, alarm limits, and emergency-stop procedure.

## Release evidence

Archive:

- `pytest` output and coverage report
- Robot `output.xml`, `log.html`, and `report.html`
- generated Libdoc HTML
- wheel and source distribution
- hardware report when a release is declared hardware-validated


## AI contract conformance

```bash
python scripts/validate_ai_contract.py
```

This check is mandatory in CI and release building.

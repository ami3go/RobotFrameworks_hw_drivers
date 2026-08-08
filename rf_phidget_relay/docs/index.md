# RF Phidget Relay 26.03

This package exposes two PhidgetInterfaceKit 0/0/4 boards as one logical
eight-channel relay bank in Robot Framework. Every keyword call is recorded
as RFDS-008 structured evidence — see [Logging and Evidence](logging_and_evidence.md).

This release implements RFDS-017 v3.0 and includes an RFDS-018 v1.0 bench
template. See `ai/` and `system_ai_contract.yaml`. Automated relay closure is
blocked while safety-critical bench details remain `UNKNOWN`.

## Connection lifecycle

1. Install the operating-system Phidget22 driver and this Python package.
2. Connect both boards by unique serial number.
3. Operate logical channels 1–8.
4. Use `Disconnect Relays` as suite teardown.

## Important semantics

`CLOSED`, `ON`, `TRUE`, and `1` mean energized/closed. `OPEN`, `OFF`, `FALSE`,
and `0` mean de-energized/open. The default `active_high=True` matches a direct
active-high output. Set `active_high=${FALSE}` only when external hardware is
inverted.

`Get Relay State` reads the commanded DigitalOutput state. It does not prove
the physical contact moved. Safety-critical systems need independent feedback.

## Bulk changes

`Set Relay Pattern` validates all eight digits before writing, but USB writes
are sequential and not electrically simultaneous. `Set Multiple Relays` also
validates its complete dictionary first. If break-before-make is required,
explicitly call `Open All Relays`, wait for the required dead time, then close
the destination relay.

## GitHub Pages

Run `python -m pip install mkdocs` and `mkdocs serve`. GitHub Pages can publish
the generated `site/` directory or use the included workflow.

# RF Phidget Relay

Robot Framework library for an 8-channel relay bank made from two
PhidgetInterfaceKit 0/0/4 devices. Version **26.03**.

Talks to the vendor Phidget22 SDK directly (`DigitalOutput` objects, one per
physical relay channel) — there is no wire protocol of its own to parse and no
bundled simulator, so hardware conformance and evidence are covered against
real boards or an injectable test double (`output_factory`) rather than a
simulated transport. Typically used to route a shared instrument (a DMM, for
example) to one of several points under test.

## Mapping

| Logical channel | Device | Physical DigitalOutput |
|---:|---|---:|
| 1–4 | Device A serial | 0–3 |
| 5–8 | Device B serial | 0–3 |

Serial numbers are deliberately mandatory: connection order is not a safe way
to distinguish two identical USB devices.

## Install

Install the Phidget22 driver from Phidgets for your operating system. Then,
from this repository root:

```console
python -m pip install -e ".[dev]"
```

Find the serial numbers printed on the devices or shown in Phidget Control
Panel, replace the example values, and run:

```console
python -m robot --outputdir results examples/02_single_channel.robot
```

## Robot Framework use

```robotframework
*** Settings ***
Library         rf_phidget_relay.PhidgetRelayLibrary
Suite Setup     Connect Relays       123456    654321
Suite Teardown  Disconnect Relays

*** Test Cases ***
Switch DMM To Channel Five
    Open All Relays
    Close Relay    5
    Relay Should Be Closed    5
```

Connecting opens all outputs by default. Disconnecting also opens all outputs
before releasing handles. This is a software safety behavior, not a substitute
for circuit protection or a hardware interlock. Opening a USB handle cannot
guarantee relay state after host power loss.

## Keywords

- `Connect Relays`, `Disconnect Relays`
- `Open Relay`, `Close Relay`, `Set Relay State`, `Get Relay State`
- `Open All Relays`, `Close All Relays`
- `Set Relay Pattern`, `Set Multiple Relays`, `Get All Relay States`
- `Pulse Relay`, `Get Relay Mapping`
- `Relay Should Be Open`, `Relay Should Be Closed`
- `Get Connection Status`, `Get Driver Information`, `Emergency Open All Relays`
- `Export Diagnostic Bundle` — zips the current RFDS-008 evidence run (see
  "Logging and evidence" below) for troubleshooting

The RFDS-017 v3.0 machine-readable contract is in `ai/phidget_relay_ai_contract.yaml`; its
integrity record is `ai/phidget_relay_ai_contract.lock`. RFDS-018 bench composition guidance
and a conservative template are in `ai/bench_integration.yaml` and
`system_ai_contract.yaml`. Unknown bench wiring remains explicitly `UNKNOWN`
until a bench owner resolves it.

See `docs/index.md`, `guide/`, and the eleven runnable examples for details.

## Logging and evidence

Every keyword call is recorded as structured, correlated RFDS-008 evidence —
arguments, duration, result/failure, and the underlying Phidget22 SDK calls —
written to `results/session/rf_phidget_relay/<run>/` (override with the
`RFDS_EVIDENCE_ROOT` environment variable). This is on by default; pass
`evidence_enabled=${FALSE}` to the `Library` import to disable it, or call
`Export Diagnostic Bundle` to zip the current run for a bug report. See
`docs/logging_and_evidence.md` for the full evidence layout and
`guide/evidence_and_diagnostics.md` for a task-oriented "my test failed, now
what" walkthrough. Validate a run's integrity (hashes, JSONL sequencing) with:

```console
python scripts/validate_evidence.py results/session/rf_phidget_relay/<run>/
```

## Running the tests

Unit tests (`tests/test_library.py`, `tests/evidence/`) use an injectable
`output_factory` test double, so they need no Phidget hardware and no vendor
SDK:

```console
python -m pip install -e ".[dev]"
python -m robot --outputdir results examples/02_single_channel.robot   # against real hardware
python -m pytest
```

`tests/hardware/verify_all_keywords.robot` is the RFDS-019 real-hardware
conformance suite: one test case per public keyword, run against two real
Phidget boards. It is tagged `hardware` and does not run in CI:

```console
python -m robot --outputdir results -v DEVICE_A_SERIAL:123456 -v DEVICE_B_SERIAL:654321 \
    tests/hardware/verify_all_keywords.robot
```

Every relay stays OPEN for the whole suite unless `-v ALLOW_CLOSE:True` is
passed, and `Close All Relays` additionally requires `-v ALLOW_CLOSE_ALL:True`
— only set these against a bench whose wiring is known safe for every channel
to be closed, alone or together (see the suite's own `Documentation` and
`ai/phidget_relay_ai_contract.yaml`'s `safety_rules`). Test Teardown and Suite
Teardown always attempt to reopen every relay regardless of how a test case
left the bank.

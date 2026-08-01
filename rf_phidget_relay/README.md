# RF Phidget Relay

Robot Framework library for an 8-channel relay bank made from two
PhidgetInterfaceKit 0/0/4 devices. Version **26.02**.

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

The RFDS-017 v3.0 machine-readable contract is in `ai/phidget_relay_ai_contract.yaml`; its
integrity record is `ai/phidget_relay_ai_contract.lock`. RFDS-018 bench composition guidance
and a conservative template are in `ai/bench_integration.yaml` and
`system_ai_contract.yaml`. Unknown bench wiring remains explicitly `UNKNOWN`
until a bench owner resolves it.

See `docs/index.md`, `guide/`, and the eleven runnable examples for details.

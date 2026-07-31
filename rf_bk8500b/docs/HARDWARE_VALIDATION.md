# Hardware Validation Plan

The automated fake-transport tests validate adapter behavior, argument conversion, keyword names, structured return values, and error propagation. They do not prove instrument firmware compatibility.

## Target matrix

Record at minimum:

| Item | Value |
|---|---|
| Load model | BK8500B exact model/rating |
| Serial number | Instrument serial |
| Firmware revision | From `Identify Electronic Load` |
| Host OS | Windows 11 / Ubuntu |
| Python | Exact version |
| Robot Framework | Exact version |
| Interface | USB-serial / RS-232 / VISA |
| Adapter/chipset | Exact model |

## Gate H1: connection and identity

- Connect/disconnect 100 cycles.
- Verify no serial-port leak.
- Confirm manufacturer, model, serial, and firmware.
- Confirm input is off after every disconnect.

## Gate H2: fixed modes with safe source

For CC, CV, CP, and CR:

- Configure while input is off.
- Enable at low energy.
- Verify setpoint readback.
- Compare voltage/current/power with a traceable DMM or source telemetry.
- Disable input and verify zero load current.

## Gate H3: fault handling

- Remove communication during read.
- Remove communication immediately after an input command.
- Trigger current/power/temperature protection using controlled limits.
- Confirm diagnostics and error queue output.
- Confirm reconnection never targets a different serial number when serial matching is enabled.

## Gate H4: long run

- Run at representative power for at least 8 hours.
- Log measurements once per second.
- Monitor communication errors, drift, instrument temperature, and host resource use.
- Confirm CSV rows are complete and timestamps are monotonic.

## Acceptance

Public production use requires all gates to pass on every supported model/firmware combination. Attach logs, Robot `output.xml`, CSV data, and diagnostic JSON to the release evidence.

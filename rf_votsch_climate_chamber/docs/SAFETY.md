# Safety Guide

Climate chambers can damage DUTs, fixtures, cables, batteries, and personnel when configured incorrectly. Treat this library as an automation interface, not as a safety controller.

## Required external controls

- Configure chamber-controller high and low alarms.
- Use independent over-temperature protection where DUT risk requires it.
- Validate airflow, condensation, humidity, pressure, and material limits.
- Ensure emergency stop access.
- Do not rely on network teardown to stop after host power loss.

## Software safeguards

- Every connection has local minimum and maximum temperature limits.
- Out-of-range setpoints fail before transmission.
- Raw protocol commands are not Robot keywords.
- Waiting has finite defaults.
- `Stop And Disconnect Climate Chamber` attempts disconnect even if stop fails.
- Hardware tests change state only after `ALLOW_CHAMBER_CONTROL=True`.

## Recommended suite pattern

```robot
Suite Setup       Connect Climate Chamber    ${IP}    ${MIN}    ${MAX}
Suite Teardown    Stop And Disconnect Climate Chamber
```

For an externally managed chamber program, use `Disconnect Climate Chamber` without stop and document who owns state restoration.

## Failure recovery

After connection loss:

1. Inspect the physical chamber state and controller display.
2. Do not assume reconnect changed or restored the setpoint.
3. Reconnect and read health, setpoint, measured temperature, and running state.
4. Stop only when doing so is safe for the DUT and chamber.
5. Record Robot logs and communication statistics.

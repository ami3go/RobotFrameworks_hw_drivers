# Safety Guide

Electronic loads can damage a DUT, wiring, fixtures, or the load itself when configured incorrectly. Treat every input-enable operation as hazardous.

## Required bench preparation

- Confirm load voltage, current, power, and resistance ratings against the exact model.
- Add an independent current-limited source or fuse where practical.
- Verify polarity before connecting the DUT.
- Use cable gauge and connectors rated for the expected continuous current.
- Confirm cooling airflow and instrument ventilation.
- Keep an accessible hardware emergency-off path.

## Recommended Robot pattern

```robot
[Setup]       Connect To Electronic Load    ${PORT}
[Teardown]    Disconnect All Electronic Loads

Configure And Enable Load    CC    1.0    current_limit=1.2    power_limit=20
Voltage Should Be Within Range    11.5    12.5
[Teardown]    Disable Electronic Load Input
```

A suite teardown should still disconnect all instruments. The library also performs suite-end cleanup, but explicit teardown makes intent visible and creates clearer logs.

## Short-circuit mode

Short mode is intentionally guarded twice:

1. Connect with `allow_short=True`.
2. Enable with `confirmation=I UNDERSTAND`.

Do not enable short mode against an energized source unless the source, wiring, connectors, and load are explicitly rated for the resulting fault current.

## Indeterminate command outcome

A communication failure after a write may mean the instrument accepted the command even though the test did not receive verification. The underlying driver reports such cases as an indeterminate outcome. The safe response is:

1. Remove or disable source energy using an independent path when possible.
2. Re-establish communication.
3. Read actual input state and configuration.
4. Do not blindly retry a hazardous write.

## Raw SCPI

`Write Raw SCPI` can bypass the adapter’s high-level sequencing. Use only in reviewed resource files and verify input state before and after any hazardous raw command.

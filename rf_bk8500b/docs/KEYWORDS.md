# BK8500BLibrary Keyword Reference

The canonical machine-readable keyword documentation is generated with Robot Framework `libdoc`. Run:

```bash
python scripts/generate_libdoc.py
```

## Connection and session keywords

- `Connect To Electronic Load`
- `Disconnect Electronic Load`
- `Disconnect All Electronic Loads`
- `Switch Electronic Load`
- `Get Active Electronic Load`
- `List Electronic Load Sessions`
- `Reconnect Electronic Load`
- `Synchronize Electronic Load State`
- `Electronic Load Should Be Connected`

## Identity, diagnostics, and status

- `Identify Electronic Load`
- `Get Electronic Load Capabilities`
- `Get Electronic Load Status`
- `Run Electronic Load Health Check`
- `Get Electronic Load Diagnostic Snapshot`
- `Export Diagnostic Snapshot`
- `Export Diagnostic Bundle` — zips the current session's live RFDS-008 evidence
  run (every keyword call and every SCPI/serial exchange, correlated and
  SHA-256-manifested); distinct from the point-in-time `Export Diagnostic
  Snapshot` above. See [Logging and evidence](logging_and_evidence.md).
- `Run Electronic Load Self Test`
- `Clear Electronic Load Status`
- `Drain Electronic Load Error Queue`

## Input, mode, setpoints, and protection

- `Set Electronic Load Mode`
- `Get Electronic Load Mode`
- `Enable Electronic Load Input`
- `Disable Electronic Load Input`
- `Electronic Load Input Should Be On`
- `Electronic Load Input Should Be Off`
- `Configure And Enable Load`
- `Set Current Setpoint` / `Get Current Setpoint`
- `Set Voltage Setpoint` / `Get Voltage Setpoint`
- `Set Power Setpoint` / `Get Power Setpoint`
- `Set Resistance Setpoint` / `Get Resistance Setpoint`
- `Set Current Protection` / `Get Current Protection`
- `Set Power Protection` / `Get Power Protection`
- `Set Remote Sense` / `Get Remote Sense`
- `Set Current Range` / `Get Current Range`
- `Set Voltage Range` / `Get Voltage Range`
- `Set Voltage Autorange` / `Get Voltage Autorange`
- `Set Current Slew Rate` / `Get Current Slew Rate`
- `Set Load Voltage Thresholds`
- `Clear Electronic Load Protection`
- `Set Short Circuit Mode`

## Measurement and assertion keywords

- `Measure Voltage`
- `Measure Current`
- `Measure Power`
- `Measure Resistance`
- `Get Measurement Snapshot`
- `Measurement Should Be Within Range`
- `Voltage Should Be Within Range`
- `Current Should Be Within Range`
- `Power Should Be Within Range`
- `Wait Until Measurement Is Within Range`
- `Log Measurements To CSV`

## Dynamic and peak operations

- `Configure Transient Load`
- `Get Transient Load Configuration`
- `Trigger Electronic Load`
- `Enable Peak Capture`
- `Clear Peak Capture`
- `Read Peak Measurements`

## State and expert operations

- `Save Electronic Load State`
- `Recall Electronic Load State`
- `Reset Electronic Load`
- `Set Electronic Load Remote`
- `Set Electronic Load Local`
- `Query Raw SCPI`
- `Write Raw SCPI`

## Return value conventions

Simple measurement keywords return a Python float, which Robot Framework treats as a number. Structured driver models are converted to dictionaries, nested lists, booleans, strings, and numeric values.

Example:

```robot
${identity}=    Identify Electronic Load
Log    Model: ${identity}[model]
Log    Serial: ${identity}[serial_number]

${result}=    Set Current Setpoint    1.0
Should Be True    ${result}[verified]
Should Be Equal As Numbers    ${result}[applied]    1.0
```

## Alias convention

The most recently connected or explicitly switched session is active. Most keywords accept `alias=<name>` as their final named argument.

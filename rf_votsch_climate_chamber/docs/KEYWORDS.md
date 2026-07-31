# Robot Keyword Reference

The authoritative generated reference can be created as HTML with `scripts/generate_docs.*`. This Markdown page groups the supported API.

## Lifecycle

| Keyword | Purpose |
|---|---|
| `Connect Climate Chamber` | Connect, verify status, and return identification. |
| `Disconnect Climate Chamber` | Optionally stop, then disconnect; idempotent by default. |
| `Stop And Disconnect Climate Chamber` | Safety teardown that attempts both operations. |
| `Reconnect Climate Chamber` | Reopen TCP connection and verify communication. |
| `Climate Chamber Should Be Connected` | Verify with a real chamber query. |
| `Get Climate Chamber Connection Statistics` | Return command and reconnect counters. |

## Identification and status

`Get Climate Chamber Identification`, `Get Climate Chamber Serial Number`, `Get Climate Chamber Model`, `Get Climate Chamber Manufacturing Year`, `Get Climate Chamber Status`, and `Get Climate Chamber Health`.

## Temperature

`Set Climate Chamber Temperature`, `Get Climate Chamber Setpoint`, `Get Climate Chamber Temperature`, `Set Climate Chamber Temperature Limits`, `Get Climate Chamber Temperature Limits`, `Start Climate Chamber`, and `Stop Climate Chamber`.

## Stabilization

### Set Temperature And Wait

Sets the target, optionally starts, requires consecutive stable samples, optionally dwells, and returns final temperature.

Important arguments:

- `target`: °C
- `dwell`: Robot time, default `0 seconds`
- `tolerance`: ±°C
- `poll_interval`: Robot time
- `timeout`: Robot time, finite by default
- `stable_samples`: consecutive samples
- `start_chamber`: Robot boolean

### Wait Until Climate Chamber Is Stable

Uses the current setpoint when `target=${NONE}` and does not start unless requested.

### Wait For Climate Chamber Dwell

Performs a finite dwell and periodically reads/logs temperature.

## Gradient and outputs

- `Set/Get Climate Chamber Heating Gradient`
- `Set/Get Climate Chamber Cooling Gradient`
- `Set/Get Climate Chamber Dryer`
- `Set/Get Climate Chamber Compressed Air`

## Assertions

- `Climate Chamber Temperature Should Be`
- `Climate Chamber Temperature Should Be Within`
- `Climate Chamber Setpoint Should Be`
- `Climate Chamber Should Be Running`
- `Climate Chamber Should Be Stopped`

## Units and values

Temperatures are °C. Gradients are °C/min. Durations accept Robot syntax such as `500 ms`, `10 s`, `5 min`, and `2 h`. Boolean arguments accept `TRUE/FALSE`, `YES/NO`, `ON/OFF`, and `1/0`.

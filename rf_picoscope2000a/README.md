# RF PicoScope2000A

Robot Framework driver for the PicoScope 2000A-family (`picosdk.ps2000a`)
oscilloscopes with a built-in AWG: **2205A MSO, 2206B/2206 MSO, 2207B/2207
MSO, 2208B/2208 MSO, 2405A**. Version **26.1**.

Built on Pico Technology's official `picosdk` Python wrapper (not
`pypicosdk`, which does not support the 2000 series — see "Why `picosdk`,
not `pypicosdk`" below). Covers connection/autodetect, per-channel
configuration (including a driver-level current-probe abstraction), trigger,
main timebase, block capture with per-channel/all-channel CSV and image
export, standard measurements (amplitude, peak-to-peak, frequency, RMS, rise/
fall time, duty cycle, and more), cross-channel timing (delay, phase), the
built-in AWG, and preset save/load.

## Install

From this repository root:

```console
python -m pip install -e "./rf_picoscope2000a[dev]"
```

Add `picosdk` (plus Pico's own native PicoSDK driver package, installed
separately from Pico Technology — `picosdk` is a ctypes wrapper around it,
not a self-contained driver) to talk to real hardware:

```console
python -m pip install -e "./rf_picoscope2000a[hardware]"
```

Add `matplotlib` for image export:

```console
python -m pip install -e "./rf_picoscope2000a[plot]"
```

## Robot Framework use

```robotframework
*** Settings ***
Library         rf_picoscope2000a.PicoScope2000ALibrary
Suite Setup     Connect    simulated=${TRUE}
Suite Teardown  Disconnect

*** Test Cases ***
Capture Channel A
    Set Channel Enabled    A    ${TRUE}
    Set Channel Range    A    5.0
    Set Trigger    A    threshold_v=0.5    direction=RISING
    Set Timebase    sample_interval_s=${0.000001}    num_samples=${1000}
    Capture Block
    ${waveform}=    Get Waveform    A
    ${frequency}=    Get Measurement    A    FREQUENCY
    Measurement Should Be Within    A    PK2Pk    1.0    3.0
    Save Waveform To CSV    ${OUTPUT DIR}/channel_a.csv    A
```

Against real hardware, omit `resource` to autodetect the single connected
unit, or pass its serial explicitly if more than one is plugged in:

```robotframework
Connect                                        # autodetect
Connect    resource=CW123/456                  # explicit serial
```

`Find Devices` lists connected serials without opening any of them.

## Keywords

- **Connection (RFDS-002):** `Connect`, `Disconnect`, `Is Connected`,
  `Get Connection State`, `Check Communication`, `Get Identity`,
  `Find Devices`, `Switch Oscilloscope`, `Get Active Oscilloscope`,
  `List Oscilloscope Connections`
- **Channel setup:** `Set/Get Channel Enabled`, `Set/Get Channel Range`,
  `Set/Get Channel Coupling`, `Set/Get Channel Offset`,
  `Set/Get Channel Probe` (voltage/current probe abstraction — see below),
  `Get Channel Settings`, `Get Enabled Channels`
- **Timebase (main time):** `Set/Get Timebase Settings`
- **Trigger:** `Set Trigger`, `Disable Trigger`, `Get Trigger Settings`
- **Capture and waveform:** `Capture Block`, `Get Waveform`,
  `Get All Waveforms`
- **Measurements** (computed host-side from the captured waveform — see
  below): `Get Measurements` (every measurement for a channel at once),
  `Get Measurement` (one named measurement), `Measurement Should Be Within`
  (assertion keyword)
- **Cross-channel timing** (see below): `Get Channel Delay`, `Get Channel
  Phase`, `Channel Delay Should Be Within`, `Channel Phase Should Be Within`
- **CSV export:** `Save Waveform To CSV` (one channel),
  `Save All Waveforms To CSV` (every captured channel, one shared time
  column)
- **Image export** (`plot` extra): `Save Channel Image` (one channel),
  `Save All Channels Image` (every captured channel, stacked subplots in one
  figure — these units have no display to screenshot, so this renders the
  decoded waveform data, not an on-device capture)
- **AWG (built-in signal generator):** `Set AWG Waveform`, `Stop AWG`,
  `Get AWG Settings` — raises if the connected model has no built-in AWG
- **Presets:** `Save Preset`, `Load Preset` — a JSON snapshot of every
  channel/trigger/timebase/AWG setting, replayed through the same public
  keywords on load
- **RFDS-008 evidence:** `Export Diagnostic Bundle`

Multiple oscilloscopes can be driven from one suite via the `alias`
parameter accepted by every non-connection keyword.

## Notes

### Why `picosdk`, not `pypicosdk`

`pypicosdk` (the package name most likely to come up when searching for a
modern Pico Python wrapper) only supports the 6000E, 3000E/5000E, and 5000D
driver families — it cannot open a 2000-series unit. The correct package for
this hardware is the older `picosdk` (`picosdk-python-wrappers`), whose
`picosdk.ps2000a` module this driver wraps.

### Current-probe support

`picosdk` itself has no probe concept — only ADC counts and a voltage range.
`Set Channel Probe` is a driver-level abstraction: `probe_type` is
`VOLTAGE` or `CURRENT`, and `scale` is native units per volt at the ADC
input. A 100 mV/A current clamp uses `scale=10`; after that, `Get Waveform`
on that channel reports amps (`unit: "A"`) instead of volts. Trigger
thresholds (`Set Trigger`'s `threshold_v`) are always the raw BNC-input
voltage regardless of probe type — real trigger hardware compares against
the physical input voltage before any probe scaling is applied.

### Standard measurements

`picosdk.ps2000a` has no on-device "immediate measurement" call — unlike a
scope with its own display/firmware, the ps2000a driver only ever returns
raw ADC block data; Pico's own PicoScope desktop *application* computes its
on-screen measurements itself, client-side, not the driver. `Get
Measurements`/`Get Measurement` do the same thing this driver already has
everything needed for, from the decoded `Get Waveform` data:
`AMPLITUDE`, `PK2Pk` (peak-to-peak), `MAXimum`, `MINImum`, `HIGH`/`LOW`
(statistical top/base levels — the histogram/modal method most scope
vendors use, not bare max/min, so `AMPLITUDE` excludes overshoot/ringing the
way a real scope's does), `MEAN`, `RMS`, `CRMs` (one-cycle RMS),
`FREQuency`, `PERIod`, `RISe`/`FALL` (10%–90% edge time), `PWIdth`/`NWIdth`
(positive/negative pulse width), `PDUty` (duty cycle), and
`POVershoot`/`NOVershoot`. Frequency/period/edge-timing measurements return
`None` (or raise, via `Get Measurement`) if the capture doesn't contain
enough edge crossings to determine them — capture more cycles of the signal
if you hit this.

### Cross-channel timing (delay, phase)

`Get Channel Delay(reference_channel, target_channel, edge=RISING)` returns
the time (seconds) from `reference_channel`'s first qualifying edge to the
nearest corresponding edge on `target_channel` — positive means the target
lags, negative means it leads. `Get Channel Phase` returns the same
relationship in degrees, using the reference channel's own measured period
as the 360° reference (the standard assumption: both signals share one
fundamental frequency). Both channels must have been enabled and captured
together in the same `Capture Block` call — every channel in one block
capture shares one sample clock, so their timestamps are already aligned,
no separate time-sync step needed. Each channel gets its own mid-reference
level computed independently, so comparing a 5 V channel against a 50 mV one
(or a voltage channel against a current-probe one) doesn't distort the
result the way a single shared threshold would.

### Timebase resolution

`ps2000a` has no direct "set sample rate" call — only an integer timebase
index whose achieved interval must be queried. `Set Timebase` resolves the
fastest timebase whose interval is at least the requested
`sample_interval_s` and returns what was actually achieved.

### AWG model gating

Not every PicoScope 2000-series unit has a built-in AWG (the plain
2104/2202/2204/2205 don't; this driver's target list above does). `Set AWG
Waveform`/`Stop AWG` check the connected model and raise a clear error
naming it if it lacks one, rather than letting the SDK call fail
cryptically.

### Real-hardware backend status

This driver was built and tested in an environment with no `pip`, no
`picosdk`, and no PicoScope hardware available. The simulated backend and
everything built on top of it (channel/trigger/timebase config, capture,
waveform decode, CSV, images, presets, AWG, every Robot keyword) is fully
implemented and unit-tested against the bundled simulator. The real-hardware
backend (`picoscope2000a.backend.RealPs2000aBackend`) is written to match
`picosdk.ps2000a`'s documented API precisely, but has not been executed
against the real SDK or a physical instrument — verify it on a machine with
`picosdk` and Pico's native driver installed before relying on it for real
captures.

## Logging and evidence

Every keyword call is recorded as structured, correlated RFDS-008 evidence —
arguments, duration, result/failure — written to
`results/session/rf_picoscope2000a/<run>/` (override with
`RFDS_EVIDENCE_ROOT`). On by default; pass `evidence_enabled=${FALSE}` to
the `Library` import to disable it, or call `Export Diagnostic Bundle` to
zip the current run for a bug report. The run is finalized when the suite
ends (`_end_suite`, this driver's Robot listener cleanup hook). Validate a
run's integrity (hashes, JSONL sequencing) with:

```console
python scripts/validate_evidence.py results/session/rf_picoscope2000a/<run>/
```

## Running the tests

```console
python -m pip install -e ".[dev]"          # unit + evidence tests, no hardware needed
python -m pytest
```

`tests/robot/smoke.robot` runs the same coverage as a Robot Framework suite
against the bundled simulator:

```console
python -m robot --outputdir results rf_picoscope2000a/tests/robot/smoke.robot
```

`tests/unit/` and `tests/evidence/` use the bundled simulator and need no
hardware or the `picosdk`/`matplotlib` extras at all — image-export tests
skip cleanly if `matplotlib` isn't installed.

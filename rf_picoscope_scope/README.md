# RF PicoScope

Robot Framework driver for PicoScope USB oscilloscopes, across multiple SDK
series via a `series` selector on `Connect`. Version **26.2**.

Currently supported:

| `series` | SDK module | Models with a built-in AWG (best-effort list — see below) |
|---|---|---|
| `"2000A"` (default) | `picosdk.ps2000a` | 2205A MSO, 2206B/2206 MSO, 2207B/2207 MSO, 2208B/2208 MSO, 2405A |
| `"3000A"` | `picosdk.ps3000a` | 3000D-series: 3204D, 3404D, 3405D (and their MSO variants) |

Built on Pico Technology's official `picosdk` Python wrapper (not
`pypicosdk`, which doesn't support either series above — see "Why
`picosdk`, not `pypicosdk`" below). Both series target Pico's "X000A"
generation of SDKs specifically — not the older, out-of-scope non-A legacy
`ps2000`/`ps3000` APIs for units like the 2104/2202/3204.

Covers connection/autodetect (per series — see "Multiple series" below),
per-channel configuration (including a driver-level current-probe
abstraction), trigger, main timebase, block capture with per-channel/
all-channel CSV and image export, standard measurements (amplitude,
peak-to-peak, frequency, RMS, rise/fall time, duty cycle, and more),
cross-channel timing (delay, phase), the built-in AWG, and preset save/load.
All of that logic is series-agnostic by design (see "Adding another series"
below) — only the low-level backend differs per series.

## Install

From this repository root:

```console
python -m pip install -e "./rf_picoscope_scope[dev]"
```

Add `picosdk` (plus Pico's own native PicoSDK driver package, installed
separately from Pico Technology — `picosdk` is a ctypes wrapper around it,
not a self-contained driver) to talk to real hardware:

```console
python -m pip install -e "./rf_picoscope_scope[hardware]"
```

Add `matplotlib` for image export:

```console
python -m pip install -e "./rf_picoscope_scope[plot]"
```

## Robot Framework use

```robotframework
*** Settings ***
Library         rf_picoscope_scope.PicoScopeLibrary
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
unit of the given `series`, or pass its serial explicitly if more than one
is plugged in:

```robotframework
Connect                                              # 2000A, autodetect
Connect    resource=CW123/456                        # 2000A, explicit serial
Connect    series=3000A                              # 3000A, autodetect
```

`Find Devices` (optionally with `series=...`) lists connected serials
without opening any of them.

## Multiple series

`"2000A"` and `"3000A"` are Pico's actual SDK module names (`ps2000a`,
`ps3000a`), not marketing series numbers — deliberately, since a plain
`"2000"`/`"3000"` would be ambiguous with the older non-A legacy APIs. Real
hardware from different series is driven by genuinely separate native
drivers with their own enumerate/open calls, so `series` can't be
autodetected the way a serial number can — pick it explicitly for real
hardware. A running session remembers which series it was opened with
(`Get Connection State`'s `transport` field, and the AWG-capable-model
check, both use it), so every other keyword just works once `Connect` has
picked the right one.

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

Multiple oscilloscopes (on the same series or different ones) can be driven
from one suite via the `alias` parameter accepted by every non-connection
keyword.

## Notes

### Why `picosdk`, not `pypicosdk`

`pypicosdk` (the package name most likely to come up when searching for a
modern Pico Python wrapper) only supports the 6000E, 3000E/5000E, and 5000D
driver families — it cannot open a 2000A- or 3000A-series unit. The correct
package for this hardware is the older `picosdk` (`picosdk-python-wrappers`),
whose `picosdk.ps2000a`/`picosdk.ps3000a` modules this driver wraps.

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

No supported series' SDK has an on-device "immediate measurement" call —
unlike a scope with its own display/firmware, these drivers only ever
return raw ADC block data; Pico's own PicoScope desktop *application*
computes its on-screen measurements itself, client-side, not the driver.
`Get Measurements`/`Get Measurement` do the same thing this driver already
has everything needed for, from the decoded `Get Waveform` data:
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

No supported series has a direct "set sample rate" call — only an integer
timebase index whose achieved interval must be queried. `Set Timebase`
resolves the fastest timebase whose interval is at least the requested
`sample_interval_s` and returns what was actually achieved.

### AWG model gating

Not every unit in a supported series has a built-in AWG (see the table at
the top — the plain, non-D 3000A-series units and the plain 2104/2202/2204/
2205 don't). `Set AWG Waveform`/`Stop AWG` check the connected model against
that series' AWG-capable list and raise a clear error naming it if it lacks
one, rather than letting the SDK call fail cryptically. The 3000A-series
list is best-effort (confirmed: the 3000D sub-series has a built-in AWG;
unconfirmed either way for plain 3000A units) — verify against Pico's
current datasheet for your exact model if it matters.

### Real-hardware backend status

This driver was built and tested in an environment with no `pip`, no
`picosdk`, and no PicoScope hardware available. The simulated backend and
everything built on top of it (channel/trigger/timebase config, capture,
waveform decode, CSV, images, presets, AWG, every Robot keyword, for both
series) is fully implemented and unit-tested against the bundled simulator.
The real-hardware backends (`picoscope_scope.backend.RealPs2000aBackend`,
`RealPs3000aBackend`) are written to match `picosdk.ps2000a`/`ps3000a`'s
documented APIs precisely, but neither has been executed against the real
SDK or a physical instrument — verify on a machine with `picosdk` and
Pico's native driver installed before relying on either for real captures.

### Adding another series (4000A, 5000A, ...)

Pico's "X000A"-generation SDKs share near-identical function signatures and
enum values (confirmed against the real `picosdk` source for both series
implemented here) — everything in `driver.py`, `measurements.py`,
`models.py`, `enums.py`, and `plotting.py` is already series-agnostic.
Adding a series is expected to be: a new `RealPsXXXXBackend` class in
`backend.py` (mechanical prefix-swap of an existing one — see its module
docstring), one line each in `driver.py`'s `_REAL_BACKEND_BY_SERIES`,
`_DEFAULT_SIMULATED_DEVICE_BY_SERIES`, and
`_AWG_CAPABLE_MODEL_SUBSTRINGS_BY_SERIES`, and a `Connect`/`Find Devices`
docstring update — not a new design.

## Logging and evidence

Every keyword call is recorded as structured, correlated RFDS-008 evidence —
arguments, duration, result/failure — written to
`results/session/rf_picoscope_scope/<run>/` (override with
`RFDS_EVIDENCE_ROOT`). On by default; pass `evidence_enabled=${FALSE}` to
the `Library` import to disable it, or call `Export Diagnostic Bundle` to
zip the current run for a bug report. The run is finalized when the suite
ends (`_end_suite`, this driver's Robot listener cleanup hook). Validate a
run's integrity (hashes, JSONL sequencing) with:

```console
python scripts/validate_evidence.py results/session/rf_picoscope_scope/<run>/
```

## Running the tests

```console
python -m pip install -e ".[dev]"          # unit + evidence tests, no hardware needed
python -m pytest
```

`tests/robot/smoke.robot` runs the same coverage as a Robot Framework suite
against the bundled simulator (both series):

```console
python -m robot --outputdir results rf_picoscope_scope/tests/robot/smoke.robot
```

`tests/unit/` and `tests/evidence/` use the bundled simulator and need no
hardware or the `picosdk`/`matplotlib` extras at all — image-export tests
skip cleanly if `matplotlib` isn't installed.

# RF TBS1000C

Robot Framework driver for the Tektronix TBS1000C digital storage
oscilloscope. Version **26.01**. Gate 2 (Core Implementation, RFDS-020):
connection, channel/trigger/acquisition configuration, calibration,
measurements, waveform fetch, screen/CSV/setup save-restore, and a raw SCPI
escape hatch are all implemented and tested against the bundled simulator.
Gate 3 (Extended Features): instrument-side waveform save/recall via
reference memory is also implemented. Gate 4 (full docs/AI contract/CI) and
Gate 5 (review/release) have not started yet — see `task/` for the driver
specification and readiness review that shaped this implementation.

## Install

From this repository root:

```console
python -m pip install -e "./rf_tbs1000c[dev]"
```

Add `pyvisa` to talk to real hardware over USBTMC:

```console
python -m pip install -e "./rf_tbs1000c[usbtmc]"
```

Run the offline acceptance suite against the bundled simulator — no scope
required:

```console
python -m robot --outputdir results rf_tbs1000c/tests/robot/acceptance.robot
```

## Robot Framework use

```robotframework
*** Settings ***
Library         rf_tbs1000c.Tbs1000cLibrary
Suite Setup     Connect    simulated=${TRUE}
Suite Teardown  Disconnect

*** Test Cases ***
Measure Channel One Frequency
    Set Channel Scale    1    0.5
    Set Trigger Source    1
    Auto Set Trigger Level
    ${frequency}=    Get Immediate Measurement    FREQuency    1
    Measurement Should Be Within    FREQuency    1    1.0    1.0E6
```

Against real hardware, pass a VISA resource string instead of
`simulated=${TRUE}`:

```robotframework
Connect    resource=USB0::0x0699::0x03C4::<serial>::INSTR
```

See `examples/` for three runnable suites (identify, configure-and-measure,
waveform-and-evidence) and `tests/robot/acceptance.robot` for the full
offline coverage.

## Keywords

- **Connection (RFDS-002):** `Connect`, `Disconnect`, `Is Connected`,
  `Get Connection State`, `Check Communication`, `Get Identity`,
  `Switch Oscilloscope`, `Get Active Oscilloscope`,
  `List Oscilloscope Connections`
- **Channel setup:** `Set/Get Channel Scale`, `Set/Get Channel Position`,
  `Set/Get Channel Offset`, `Set/Get Channel Coupling`,
  `Set/Get Channel Bandwidth Limit`, `Set/Get Channel Probe Gain`,
  `Set/Get Channel Name`, `Get Channel Settings`
- **Trigger:** `Set/Get Trigger Source`, `Set/Get Trigger Slope`,
  `Set/Get Trigger Coupling`, `Set/Get Trigger Level`,
  `Auto Set Trigger Level`, `Force Trigger`, `Get Trigger Settings`
- **Acquisition:** `Run Autoset`, `Start Acquisition`, `Stop Acquisition`,
  `Set/Get Acquisition Mode`, `Get Acquisition Count`
- **Calibration:** `Run Internal Calibration`, `Get Calibration Status`,
  `Get Calibration Results` — never run implicitly by any other keyword
- **Measurement and waveform:** `Get Immediate Measurement`,
  `Measurement Should Be Within`, `Get Waveform`, `Save Screen Image`,
  `Save Waveform To CSV`, `Save Waveform To CSV On Instrument`,
  `Save Waveform To Reference Memory` (instrument-side, no host file
  transfer), `Recall Waveform From Host File` (uploads a host file and
  loads it into reference memory — Gate 3)
- **Setup save/restore:** `Save Setup`, `Restore Setup`,
  `Save Setup To Instrument Memory`, `Restore Setup From Instrument Memory`,
  `Restore Factory Setup`
- **Raw SCPI escape hatch:** `Enable Raw SCPI` (requires the exact
  confirmation text `"ENABLE RAW SCPI"`), `Raw SCPI Query`, `Raw SCPI Write`

Multiple oscilloscopes can be driven from one suite via the `alias`
parameter accepted by every non-connection keyword.

## Notes

- `Restore Setup` verifies the resent `*LRN?` string via the instrument's
  error queue rather than assuming success.
- Waveform decoding trusts only the declared IEEE-488.2 binary-block length —
  it never strips the raw sample bytes, since a legitimate sample value can
  equal a whitespace byte.
- An `ai/ai_contract.yaml` (RFDS-017 machine-readable contract) has not been
  generated yet; that is Gate 4 work.

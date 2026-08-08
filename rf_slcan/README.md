# RF SLCAN

Robot Framework driver for SLCAN (serial-line CAN) interface adapters — USB/serial devices
that bridge a host to a physical CAN bus using the Lawicel CANUSB/CAN232-style ASCII protocol,
also implemented by CANable/candleLight firmware, the Linux kernel `slcan` driver, and
`python-can`'s `slcan` interface. Version **26.2**. Gate 1-2 (Architecture, Skeleton, Core
Implementation, RFDS-020): connection, bitrate/channel control, sending and receiving CAN
frames (including asynchronous frame capture via a background reader thread), status/version/
serial-number queries, and a raw SLCAN escape hatch are all implemented and tested against the
bundled simulator. Gate 3 (Extended Features): the acceptance code/mask filter (`M`/`m`) and
timestamp mode (`Z0`/`Z1`) are also implemented. Every keyword call is also recorded as RFDS-008
structured evidence, and `tests/hardware/verify_all_keywords.robot` provides RFDS-019
real-hardware conformance (see "Logging and evidence" and "Hardware tests" below). Gate 4 (full
docs/AI contract/CI) and Gate 5 (review/release) have not started yet — see `task/` for the
driver specification that shaped this implementation.

**Scope**: classic CAN 2.0 only (11-bit/29-bit arbitration IDs, 0-8 byte data, remote/RTR
frames). CAN FD is deliberately out of scope — there is no single agreed FD dialect across
SLCAN implementations to ground it in.

## What makes this driver different

Every other driver in this repository is pure query/response: send a command, read exactly
the line that answers it. SLCAN can't work that way, because the adapter can push a line onto
the serial port representing a **received CAN frame at any moment** — including while a
command this driver just sent is still awaiting its own acknowledgement. This driver runs a
background reader thread (`slcan/reader.py`) that continuously classifies every line from the
adapter and routes it to either the receive-frame queue or the currently in-flight command's
result slot, so frames arriving between keyword calls (or mid-command) are captured correctly
rather than lost or misinterpreted as an ack. See `slcan/reader.py`'s module docstring and the
task document §5/§6 for the full design rationale.

## Install

From this repository root:

```console
python -m pip install -e "./rf_slcan[dev]"
```

Add `pyserial` to talk to a real SLCAN adapter (a USB-CDC virtual COM port on most modern
CANable/CANUSB-style devices):

```console
python -m pip install -e "./rf_slcan[serial]"
```

Run the offline acceptance suite against the bundled simulator — no adapter required:

```console
python -m robot --outputdir results rf_slcan/tests/robot/acceptance.robot
```

## Robot Framework use

```robotframework
*** Settings ***
Library         rf_slcan.SlcanLibrary
Suite Setup     Connect    simulated=${TRUE}
Suite Teardown  Disconnect

*** Test Cases ***
Send And Receive A Frame
    Set Bitrate    500K
    Open Channel    NORMAL
    Send Frame    291    AABBCC
    ${frame}=    Receive Frame    timeout_s=1
    Log    ${frame}
    Close Channel
```

Against real hardware, pass a serial port path instead of `simulated=${TRUE}`:

```robotframework
Connect    resource=/dev/ttyACM0
```

(or `COM5` on Windows). See `examples/` for five runnable suites (identify, open and transmit,
receive frames, status and error handling, acceptance filter and timestamps) and
`tests/robot/acceptance.robot` for the full offline coverage.

## Keywords

- **Connection (RFDS-002):** `Connect`, `Disconnect`, `Is Connected`, `Get Connection State`,
  `Check Communication`, `Get Identity` (synthesized from `V`/`N` — there is no `*IDN?`
  equivalent in the base protocol), `Switch Adapter`, `Get Active Adapter`,
  `List Adapter Connections`
- **Channel control:** `Set Bitrate` (`10K`/`20K`/`50K`/`100K`/`125K`/`250K`/`500K`/`800K`/
  `1M`, or a raw `S<n>` index), `Open Channel` (`NORMAL`/`LISTEN_ONLY`), `Close Channel`,
  `Is Channel Open`
- **Frames:** `Send Frame` (`data` accepts bytes, a list of ints, or a hex string),
  `Receive Frame` (blocks up to a timeout, returns `${None}` on nothing arriving),
  `Drain Received Frames`, `Get Received Frame Count`, `Clear Received Frames`,
  `Get Receive Overflow Count` (read-only)
- **Status:** `Get Status`, `Get Version`, `Get Serial Number`
- **Acceptance filter (Gate 3):** `Set/Get Acceptance Code`, `Set/Get Acceptance Mask` —
  rejected by the adapter while the channel is open, mirroring `Set Bitrate`. Both `Get`
  keywords are read-only, driver-tracked round trips: the adapter has no query form for
  either, so they simply report what this driver last successfully set (`${None}` if never
  set).
- **Timestamp mode (Gate 3):** `Set/Get Timestamps Enabled` — when enabled, frames returned
  by `Receive Frame`/`Drain Received Frames` carry a populated `timestamp_ms` field instead
  of `${None}`.
- **Raw escape hatch:** `Enable Raw SLCAN` (requires the exact confirmation text
  `"ENABLE RAW SLCAN"`), `Raw SLCAN Command`
- **Diagnostics:** `Export Diagnostic Bundle` — zips the current suite's RFDS-008 evidence
  run (see "Logging and evidence" below) for troubleshooting

Multiple adapters can be driven from one suite via the `alias` parameter accepted by every
non-connection keyword.

## Logging and evidence

Every keyword call is recorded as structured, correlated RFDS-008 evidence — arguments,
duration, result/failure, and the actual SLCAN ASCII lines exchanged with the adapter
(including asynchronously received CAN frames) — written to
`results/session/rf_slcan/<run>/` (override with the `RFDS_EVIDENCE_ROOT` environment
variable). On by default; pass `evidence_enabled=${FALSE}` to the `Library` import to
disable it, or call `Export Diagnostic Bundle` to zip the current run for a bug report. See
`docs/logging_and_evidence.md` for the full evidence layout and
`guide/evidence_and_diagnostics.md` for a task-oriented "my test failed, now what"
walkthrough. Validate a run's integrity (hashes, JSONL sequencing) with:

```console
python scripts/validate_evidence.py results/session/rf_slcan/<run>/
```

## Hardware tests

`tests/hardware/verify_all_keywords.robot` exercises every one of this library's public
keywords against a real SLCAN adapter and checks its response — one test case per keyword
(RFDS-019). It is tagged `hardware` and does not run in CI:

```console
python -m robot --outputdir results -v RESOURCE:/dev/ttyACM0 tests/hardware/verify_all_keywords.robot
```

(or `-v RESOURCE:COM5` on Windows). The channel stays CLOSED for the whole suite unless
`-v ALLOW_OPEN:True` is passed, and `Send Frame` additionally requires `-v
ALLOW_TRANSMIT:True` — transmitting puts a real frame on a real CAN bus, which can disrupt
other devices sharing it, so only set this against a bench known to tolerate test traffic.
Without `ALLOW_TRANSMIT`, a channel opened under `ALLOW_OPEN` opens `LISTEN_ONLY` instead,
so receive-path keywords can still be exercised passively. Suite Teardown always closes the
channel and disconnects, whatever state a test case left things in.

## Running the tests

```console
python -m pip install -e "./rf_slcan[dev,serial]"
python -m pytest                                                    # unit + evidence tests, no hardware
python -m robot --outputdir results tests/robot/acceptance.robot    # offline, against the bundled simulator
python -m robot --outputdir results -v RESOURCE:/dev/ttyACM0 \
    tests/hardware/verify_all_keywords.robot                        # RFDS-019, real adapter required
```

## Safety-relevant behaviors

- **Closing the channel is always possible**, even mid-fault or when the driver's own state
  already believes the channel is closed — `Close Channel` never pre-validates client-side
  before sending `C`, so a bus left in an unknown state is never unreachable because of
  bookkeeping getting out of sync with the adapter's real state.
- **The channel cannot be opened before a bitrate is set.** This is a documented, conservative
  judgment call (fail-closed rather than opening at an undefined bitrate) — see the task
  document §16 for why, and revisit if a specific target adapter is confirmed to behave
  differently.
- **Listen-only mode actually prevents transmission** — `Send Frame` while the channel is open
  in `LISTEN_ONLY` mode raises a typed error rather than silently attempting to transmit.
- **A full receive queue degrades predictably**: the oldest queued frame is dropped and a
  queryable overflow counter (`Get Receive Overflow Count`) is incremented — never silent,
  never unbounded growth, never a blocked reader thread.
- **A lost connection surfaces promptly.** The background reader detects a transport fault
  (e.g. the adapter is unplugged) and marks the session accordingly, so any in-flight or
  subsequent command/receive call raises `SlcanConnectionError` immediately rather than only
  ever timing out silently.
- The exact `F` status-flag bit layout (bus-off, error-passive, arbitration-lost, etc.) is
  drawn from the widely-mirrored Lawicel protocol description but has not been re-confirmed
  against a specific target adapter's manual — see the task document §16 item 1 before relying
  on `Get Status` for real bus-fault detection on a particular unit.
- **The acceptance code/mask filter (Gate 3) is not confirmed as universally supported or
  identically behaved across adapters** — some real adapters may ignore `M`/`m` entirely and
  silently ACK rather than actually filtering. The bundled simulator exercises the typed
  keyword round trip only; it does not enforce filtering against injected test frames, since
  hardware-accurate filtering behavior was never confirmed against a specific target adapter.
  Confirm against your specific adapter's manual before relying on this for real bus-load
  reduction.
- **Timestamp mode (Gate 3) uses a 4-hex-digit, 60000&nbsp;ms-wrapping counter** per the
  widely-mirrored protocol description — also not independently re-confirmed against a
  specific target adapter (task document §16). Enabling/disabling it mid-session only affects
  frames the adapter reports afterward; already-queued frames keep whatever timestamp state
  was in effect when they arrived.
- An `ai/ai_contract.yaml` (RFDS-017 machine-readable contract) has not been generated yet;
  that is Gate 4 work.

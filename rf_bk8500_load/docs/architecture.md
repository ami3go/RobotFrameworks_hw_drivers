# Architecture


## Verified implementation boundary

The transport/driver/library path shown below passed 56/56 physical Robot
Framework tests on model 8500 firmware 1.84. Release 26.16 preserves the verified v26.14 frame transaction path and adds
ordered baud probing in the connection layer. The report confirms callability and readback but does
not substitute for raw RFDS-019 per-keyword protocol traces.

## Layering

```
  Robot Framework suite  (atest/*.robot)
            │  keywords
  ┌─────────▼──────────────────────────────────────────┐
  │ BK8500Library        library.py                    │  keyword names, argument
  │                                                    │  conversion, oracles,
  │                                                    │  multi-connection aliases
  ├────────────────────────────────────────────────────┤
  │ BK8500Driver         driver.py                     │  instrument semantics,
  │                                                    │  SI units, validation,
  │                                                    │  safety rules, retries
  ├──────────────────────┬─────────────────────────────┤
  │ protocol.py          │ enums.py / exceptions.py    │  frame codec, command
  │                      │                             │  table, status decoding
  ├──────────────────────┴─────────────────────────────┤
  │ Transport            transport.py                  │  26 bytes in, 26 out
  │   SerialTransport            SimulatedTransport    │
  └──────────┬───────────────────────┬─────────────────┘
             │ pyserial              │ in-process instrument model
        real instrument         no hardware
```

Each layer only knows about the one below it:

* **protocol.py** knows bytes. No units, no state, no policy. Pure functions
  plus two enums, so it is trivially testable.
* **transport.py** knows how to move one frame and get one frame back. It has
  no idea what a mode or a setpoint is. Swapping the real instrument for the
  simulator is a constructor argument, not a code change.
* **driver.py** owns everything instrument-specific: unit scaling, parameter
  validation against the model's rated envelope, response status checking,
  retries, and the safety rules that cannot be delegated to the hardware.
* **library.py** owns everything Robot-specific: keyword names, string to enum
  conversion, dictionaries instead of dataclasses, verification keywords that
  raise `AssertionError` subclasses, and the connection alias cache.

## Why the driver layer is separate from the keyword layer

The keyword layer is a translation shim, roughly one line per keyword. All the
behaviour worth testing lives in `BK8500Driver`, which imports nothing from
Robot Framework. That makes the interesting logic testable with plain pytest,
usable from a bare script or a bench orchestration service, and it keeps the
keyword names free to change without touching instrument semantics.

## The simulator is a first-class component

`SimulatedTransport` implements the register set this driver uses and computes
readings from a Thévenin source (`source_voltage_v` behind
`source_resistance_ohm`), so CC, CV, CW and CR all produce physically
consistent voltage, current and power. It also enforces the parts of the
instrument's own state machine that matter for test correctness: the input
cannot be closed without remote control, a bus trigger is rejected unless the
trigger source is BUS, an out-of-range partition value is rejected with status
`0xA0`.

That is enough to exercise keyword names, argument handling, sequencing,
teardown and error paths in CI with no hardware. It is **not** enough to
validate a measurement: see limitation LIM-9 in the contract.

## Error strategy

One exception family (`BK8500Error`) with a class per failure mode, so a suite
can catch broadly and a planner can branch precisely. Three rules:

1. **Fail locally when possible.** An out-of-range setpoint raises
   `BK8500ValidationError` before a frame is built, so no instrument state
   changes and the message can name the model and the permitted range.
2. **Never silently succeed.** Every response is checked for framing and
   checksum; every status frame is decoded; a non-success status raises.
3. **Retry only what is worth retrying.** Framing errors, checksum errors,
   wrong-address replies and timeouts are transient and are retried up to three
   times; the transport flushes the input buffer before each write so a late
   frame cannot be read as the next reply. A rejected command
   (`BK8500CommandError`) means the instrument understood and refused, so
   retrying it just repeats the mistake.
4. **Refuse to guess.** Where a reply is genuinely ambiguous — a status frame
   with no payload answering a read — the driver raises instead of returning a
   plausible-looking number. A wrong measurement is worse than a failed one.

## Safety model

The instrument's own protection limits are the primary defence and are set in
suite setup. The driver adds three things the instrument cannot do:

* **Envelope validation** against the model table, including a conservative
  fallback when the model is unknown.
* **A remote-control interlock**: `Load Input On` refuses to run unless remote
  control was claimed in this session, so a suite cannot energise a load it
  does not actually control.
* **A SHORT guard**: the SHORT function is only reachable through a separate,
  explicitly named keyword, so an AI-generated or copy-pasted test cannot
  select it by accident.

What the driver deliberately does *not* do is guess. It does not clear
protection faults, does not derate on its own, and does not know the DUT's
rating. Those are bench-level facts and belong in an RFDS-018 bench contract.

## Concurrency

One `BK8500Driver` per serial port; `SerialTransport` holds a lock around each
transaction so a stray parallel call cannot interleave half a frame. The
library scope is `GLOBAL` and several instruments can be open at once under
different aliases, but keywords against a single alias must not be called
concurrently: the protocol has no framing recovery and a lost byte
desynchronises the link until the port is reopened.

## File map

| Path | Contents |
|------|----------|
| `bk8500_load/protocol.py` | Frame codec, command table, status codes, unit constants |
| `bk8500_load/transport.py` | `Transport` base, `SerialTransport`, `SimulatedTransport` |
| `bk8500_load/driver.py` | `BK8500Driver`: semantics, validation, safety, retries |
| `bk8500_load/library.py` | `BK8500Library`: Robot keywords and oracles |
| `bk8500_load/enums.py` | Modes, functions, triggers, state registers, model limits, data models |
| `bk8500_load/exceptions.py` | Error catalogue |
| `BK8500Library.py` | Legacy import shim so suites can write `Library    BK8500Library`; the canonical import is `rf_bk8500_load.BK8500Library` (see `rf_bk8500_load/__init__.py`) |
| `ai/bk8500_load_ai_contract.yaml` | Root-level RFDS-017 v3.0 machine contract; installed as wheel data under `share/rf_bk8500_load/ai` |
| `ai/bk8500_load_ai_contract.lock` | SHA-256 of the contract and of the keyword surface |
| `atest/` | Robot Framework conformance suite and shared resource file |
| `tests/` | pytest unit and contract-conformance tests |
| `tools/generate_lock.py` | Regenerates the lock file |

## Automatic baud probe architecture

`BK8500Library.open_load_connection()` parses Robot arguments and delegates to
`BK8500Driver.connect_serial_with_baud_detection()`. The driver creates one
normal `SerialTransport` per candidate, so framing, checksum, address, echo and
identity validation are identical to ordinary operation. Failed candidates are
closed; the successful driver instance remains connected. The transport layer
contains no special probing mode and the protocol layer is unchanged.

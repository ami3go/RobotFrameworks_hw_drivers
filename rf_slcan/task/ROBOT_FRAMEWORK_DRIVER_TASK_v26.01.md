# Task: Robot Framework Driver for SLCAN Interface Adapters

**Task revision:** 26.01-draft
**Date:** 2026-08-02
**Target package:** `rf_slcan_v26.01.zip`
**Required internal repository root:** `rf_slcan/`

## 1. Objective

Create a Robot Framework library for SLCAN (serial-line CAN) interface adapters — USB/serial
devices that bridge a host to a physical CAN bus using the Lawicel CANUSB/CAN232-style ASCII
protocol, also implemented by CANable/candleLight firmware, the Linux kernel `slcan` driver,
and `python-can`'s `slcan` interface. Built on a new typed Python core driver (`slcan`) that
owns SLCAN command construction/parsing and, uniquely among this repository's drivers, a
background reader thread.

This instrument class is fundamentally different from every driver already in this
repository: it is not a query/response instrument. The adapter can push a line onto the
serial port representing a received CAN frame at **any** moment, including while a command
this driver just sent is still awaiting its own acknowledgement. No existing driver here has
had to handle unsolicited/asynchronous data, so this is new architecture for the platform —
see §5 and the core driver's `reader.py` module.

This package shall build the RFDS-002 canonical connection lifecycle
(`Connect` / `Disconnect` / `Is Connected` / `Get Connection State` / `Check Communication` /
`Get Identity`) as the **primary, documented API** from the outset, matching every other
driver in this repository — not retrofitted later.

**Scope for v26.01**: classic CAN 2.0 only (11-bit/29-bit arbitration IDs, 0-8 byte data,
remote/RTR frames). CAN FD is explicitly **out of scope** — there is no single agreed FD
dialect across SLCAN implementations, so adding it now would mean guessing at one vendor's
extension rather than grounding it in a confirmed source. Acceptance filter/mask commands
(`M`/`m`), timestamp mode (`Z0`/`Z1`), and additional status detail are deferred to a future
Gate 3 pass.

## 2. Protocol facts (source: the Lawicel CAN232/CANUSB ASCII protocol — the de facto standard
essentially every "slcan" implementation agrees on, cross-referenced against the Linux kernel
`drivers/net/can/slcan/slcan-core.c` driver and `python-can`'s `can.interfaces.slcan` module
for the command/response shapes that are consistent across all three; **the exact `F` status-
flag bit assignments should be re-confirmed against the specific target adapter's own manual
before Gate 2 hardware qualification** — they are widely, but not universally, documented
identically across vendors)

- **Transport:** a serial byte stream — a physical RS-232 adapter or, far more commonly, a
  USB-CDC virtual COM port (CANUSB, CANable, most modern USB-CAN dongles). One `pyserial`
  backend covers both; no VISA involvement (this is not a SCPI instrument).
- **Command grammar:** every command is one ASCII line terminated by `\r` (CR). The adapter
  acknowledges a command with a bare `\r` (empty body) or rejects it with a bare `\a` (BEL,
  0x07) — sent standalone, **not** CR-terminated, which the transport/reader must handle as
  its own terminator alongside CR (§5).
- **Channel control:** `S<n>` sets the nominal CAN bitrate (`n` = 0-8 for
  10k/20k/50k/100k/125k/250k/500k/800k/1M), must be sent before `O`/`L`. `O` opens the channel
  in normal mode; `L` opens it in listen-only mode (receive-only, never transmits or
  acknowledges bus frames — useful for passive bus monitoring without disturbing traffic).
  `C` closes the channel; documented behavior on real adapters is that closing is always
  accepted, which this driver's simulator and safety requirements (§6) treat as load-bearing,
  not incidental.
- **Frame transmission/reception**, the same wire shape in both directions: `t<id:3hex>
  <dlc:1hex><data:0-16hex>` (standard data frame), `T<id:8hex><dlc:1hex><data:0-16hex>`
  (extended data frame), `r<id:3hex><dlc:1hex>` (standard remote/RTR frame, no data), `R<id:
  8hex><dlc:1hex>` (extended remote/RTR frame, no data). A frame the host sends and a frame
  the adapter reports as received off the bus look identical on the wire — only which
  direction it travels differs.
- **Status:** `F` queries status flags, returned as `F<hex-byte>`. Bit layout as commonly
  documented: bit0 RX queue full, bit1 TX queue full, bit2 error warning, bit3 data overrun,
  bit4 reserved/unused, bit5 error passive, bit6 arbitration lost, bit7 bus error — **verify
  against the target adapter's manual during Gate 2** (§19).
- **Identity:** `V` returns hardware/software version as `V<hw:2hex><sw:2hex>`; `N` returns a
  serial number as `N<4hex>`. Neither is a real `*IDN?` equivalent — there is no manufacturer/
  model string in the base protocol, so `Get Identity` synthesizes a stable identity string
  from these two responses (§7).
- **Not implemented in v26.01** (see also §1's scope note): `Z0`/`Z1` timestamp mode,
  `M`/`m` acceptance code/mask filters, CAN FD extensions of any vendor's dialect.

## 3. Mandatory package structure

```text
rf_slcan/
├── rf_slcan/                Robot Framework Python library (adapter)
├── slcan/                   new typed core driver: transport, codec, background reader
├── examples/                Robot suites
├── tests/                   Python unit tests, Robot acceptance tests
├── task/                    this file
├── README.md
├── pyproject.toml
└── LICENSE
```

No `src/` directory is permitted (RFDS-005 §6.1). This is the same simplified structure
(two top-level packages, not RFDS-005 §6's full canonical single-nested-package tree) already
used by `rf_tbs1000c`, `rf_agilent33220a`, `rf_agilent34411a`, and `rf_ea_ps9000t` for their
Gate 1-3 work — full RFDS-005 compliance (`ai/`, `config/`, `history/`, `review/`, `docs/`,
`guide/`, CI workflows, ≥10 examples) is deferred to Gate 4/5, matching those drivers.

## 4. Versioning and packaging

1. ZIP filename shall be `rf_slcan_v26.01.zip`.
2. ZIP shall contain exactly one top-level folder named `rf_slcan`.
3. Human-facing release label shall be `v26.01`.
4. Python distribution version shall be PEP 440-compatible `26.1`.
5. Distribution name: `robotframework-slcan`.
6. The Python import shall be `rf_slcan`.
7. The primary Robot import shall be:

```robot
Library    rf_slcan.SlcanLibrary
```

## 5. Architecture

### 5.1 Layers

1. **Robot Framework layer** — keyword names, Robot-friendly argument conversion (bitrate
   names, hex/list/bytes data), RFDS-002 connection-state dictionary, cleanup (critically
   including stopping the background reader thread — see §5.2).
2. **Typed Python driver layer** (`slcan`) — command construction/parsing (`codec.py`),
   channel/frame/status models, the command choke-point (`driver.py`'s `_send_command`).
3. **Background reader** (`reader.py`) — a daemon thread that continuously reads lines from
   the transport and routes each one to either the receive-frame queue (an unsolicited CAN
   frame) or the pending-command result slot (an ack, a nack, or a query's data response).
   This is the module that makes asynchronous frame capture possible; no other driver in this
   repository has an equivalent component.
4. **Transport layer** — `pyserial`, plus a deterministic in-process simulator whose
   `read_until` blocks on an internal queue the same way a real serial port blocks on the OS,
   so the reader thread exercises identical logic against both.
5. **Instrument layer** — the physical SLCAN adapter and whatever CAN bus it's attached to.

### 5.2 Design constraints

- Robot keywords shall not duplicate SLCAN command formatting; that belongs in `slcan.codec`.
- Exceptions shall follow RFDS-007: an `SlcanError`-rooted hierarchy (`SlcanConnectionError`,
  `SlcanTimeoutError`, `SlcanProtocolError`, `SlcanDeviceError`, `SlcanBusError`,
  `SlcanValidationError`, `SlcanConfigurationError`), not bare built-ins raised at the keyword
  boundary.
- **Commands must be serialized one at a time** (`driver.py`'s `_command_lock`), and any
  stale, undelivered result from a previously-timed-out command must be drained before
  sending a new one — SLCAN gives no per-command tag on its acks, so without this a late ack
  for an abandoned command could be mistaken for a different command's ack.
- **The background reader thread's lifecycle is owned entirely by `SlcanAdapter`**: started in
  `connect_serial`/`connect_simulated`, stopped (with a bounded join, never blocking
  `Disconnect` forever) in `close()`, before the transport itself is closed. The Robot
  adapter's `_end_suite` listener hook is the safety net that guarantees no thread survives a
  suite that forgets `Disconnect`.
- A raw escape hatch (`Enable Raw SLCAN` / `Raw SLCAN Command`) shall exist, guarded by an
  exact confirmation string (`"ENABLE RAW SLCAN"`) distinct from every other driver's raw-
  protocol confirmation phrase, consistent with this repository's established two-tier-guard
  convention.

## 6. Safety requirements

CAN-bus-specific hazards are different in kind from the electrical/signal-integrity hazards
covered by this repository's power-supply/load/generator drivers — the risks here are about
correctly representing bus state and never leaving the driver's internal model out of sync
with the adapter's real state.

1. **Closing the channel must always be possible**, even mid-fault or when the driver's own
   state already believes the channel is closed. `Close Channel` shall not pre-validate
   client-side "is it open" state before sending `C` — always attempt it, so a bus in an
   unknown or faulted state is never left unreachable by driver bookkeeping getting out of
   sync with reality.
2. **Bus-off / error-passive / arbitration-lost conditions must be surfaced as a typed
   `SlcanBusError`**, never silently absorbed into a generic device error or ignored — a
   caller distinguishing "my last command was rejected" from "the bus itself is faulting"
   needs different remediation.
3. **A full receive queue must degrade predictably, not silently or by blocking the reader
   thread forever**: drop the oldest queued frame and increment a documented, queryable
   overflow counter (`Get Receive Overflow Count`) rather than either growing unbounded or
   stalling frame capture.
4. **Listen-only mode must actually prevent transmission** — `Send Frame` while the channel is
   open in `LISTEN_ONLY` mode shall fail with a typed error, not silently attempt to transmit
   (which listen-only adapters typically reject at the hardware level anyway, but the driver
   should not rely on that alone).
5. **A lost connection (adapter unplugged, transport error) must surface promptly on the next
   call**, not hang until an unrelated timeout — the background reader detects a transport
   fault and marks the connection accordingly (`reader.py`'s fault-sentinel mechanism), so any
   in-flight or subsequent command/receive call raises `SlcanConnectionError` immediately
   rather than only ever timing out silently.

## 7. Required connection keywords (RFDS-002 canonical, primary API)

- `Connect(resource=None, alias="default", timeout_s=None, **options)` → RFDS-002 §12.1
  connection-state dictionary. `resource` is a serial port path (e.g. `/dev/ttyACM0` or
  `COM5`); omit for the bundled simulator (`resource=None` + `options[simulated]=True`).
- `Disconnect(alias=None)` — idempotent; also stops the background reader thread.
- `Is Connected(alias=None)` → bool, never raises for a missing session.
- `Get Connection State(alias=None, refresh=False)` → RFDS-002 §12.1 dictionary.
- `Check Communication(alias=None)` → bool, raises on failure (issues `V`).
- `Get Identity(alias=None, refresh=True)` → stable identity string synthesized from `V`/`N`
  (there is no `*IDN?` equivalent in the base protocol — see §2).
- `Switch Adapter` / `Get Active Adapter` / `List Adapter Connections` — multi-alias sessions,
  matching every other multi-instrument package in this repository.

## 8. Channel control keywords

- `Set Bitrate {10K|20K|50K|100K|125K|250K|500K|800K|1M}` — `S<n>`. Rejected by the adapter
  while the channel is open (§2).
- `Open Channel(mode="NORMAL")` — `O` (normal) or `L` (listen-only). Rejected by the adapter
  if no bitrate has been set first (a documented, conservative judgment call — see §19).
- `Close Channel` — `C`. Always attempted; see §6 item 1.
- `Is Channel Open` — read-only, driver-tracked state (mirrors what the last successful
  open/close call established; the adapter itself has no "query current mode" command).

## 9. Frame keywords

- `Send Frame(arbitration_id, data=b"", extended=False, remote=False)` — validates ID range
  (0-0x7FF standard / 0-0x1FFFFFFF extended) and data length (0-8 bytes, matching `dlc`)
  client-side before any device I/O, raising `SlcanValidationError` on violation.
- `Receive Frame(timeout_s=1.0)` → a frame dict or `${None}` on timeout. Receiving nothing
  within the timeout is a normal outcome, not an error — this keyword never raises for a quiet
  bus.
- `Drain Received Frames(max_count=None)` → a list of frame dicts, non-blocking, matching this
  repository's established reading-memory FIFO drain-keyword pattern
  (`rf_agilent34411a`'s `Drain Readings`).
- `Get Received Frame Count` / `Clear Received Frames` / `Get Receive Overflow Count`
  (read-only — §6 item 3).

## 10. Status / identity keywords

- `Get Status` → a dict of the parsed `F` flags, including a convenience `has_fault` field.
- `Get Version` / `Get Serial Number` — `V`/`N`, both harmless read-only queries that don't
  require the channel to be open.

## 11. Raw SLCAN escape hatch

- `Enable Raw SLCAN` shall require an exact confirmation string (`"ENABLE RAW SLCAN"`),
  distinct from every other driver's raw-protocol confirmation phrase (§5.2).
- `Raw SLCAN Command(command, expects_data=False)` shall document that it bypasses typed
  validation.

## 12. Simulator requirements

The bundled simulator (`SimSlcanAdapter`) shall support, deterministically and without
hardware:

- Bitrate/open/close state tracking, including the adapter's documented rejections (bitrate
  change while open; open without a bitrate set first — §19; open while already open; transmit
  while not open or while in listen-only mode).
- `F`/`V`/`N` status/version/serial-number responses, with `status_flags` directly settable by
  a test as a raw byte (test hook, not a driver keyword) so `has_fault`-adjacent behavior can
  be exercised offline.
- **`inject_frame(frame)`** — a test-only hook (not a Robot keyword) that simulates another
  node putting a frame on the bus, pushed through the same internal queue the simulator's own
  command acks flow through, so the driver's background reader thread exercises the exact same
  code path against the simulator as it would against real hardware. This is the single most
  important simulator requirement for this driver, since it's the only way to test
  asynchronous frame capture offline.

## 13. Tests

### 13.1 Python unit tests

Cover at minimum:

1. Simulator connect and identity (`V`/`N` synthesis).
2. Channel cannot open before a bitrate is set; bitrate cannot change while open; opening
   twice is rejected.
3. Closing is always possible, including when the driver's own state already believes the
   channel is closed (§6 item 1).
4. Standard/extended/remote frame transmission, and client-side validation of ID range and
   data length before any device I/O.
5. Transmission is rejected while the channel isn't open, and while open in listen-only mode
   (§6 item 4).
6. **A frame injected while no keyword is actively running is still captured** by the
   background reader and later drained — the core "asynchronous, not just synchronous"
   correctness property.
7. **A frame injected between a command's write and its own acknowledgement is routed to the
   receive queue, never mistaken for that command's ack** — the core interleaving-safety
   property this driver's whole architecture exists to guarantee.
8. Receive-queue overflow drops the oldest frame and increments the documented counter
   (§6 item 3), rather than growing unbounded or blocking the reader thread.
9. A reader-thread fault (simulated transport failure) surfaces as `SlcanConnectionError` on
   the next call, rather than only ever timing out silently (§6 item 5).
10. The background reader thread actually stops, promptly, on `close()`/`Disconnect` — a
    leaked or wedged thread shall fail the test, not hang the suite.
11. Raw SLCAN guard (rejects without exact confirmation text; a nack surfaces as
    `SlcanDeviceError`).
12. Robot data-conversion helpers (dataclass/enum/bytes → dict/list/scalar; bitrate-name,
    mode-name, and hex/list/bytes data argument normalization).
13. Multi-alias session handling, including `_end_suite` closing every session (and therefore
    stopping every reader thread) at suite teardown.

### 13.2 Robot acceptance tests

Must run offline against the simulator and cover: identity, connect/disconnect lifecycle
(including the RFDS-002 generic keywords), the open-before-bitrate rejection, a full bitrate/
open/close round trip, sending standard and extended frames, the receive-timeout contract
(`${None}` on nothing arriving), status/version/serial-number queries, and the raw SLCAN
escape hatch. (Frame-injection/interleaving correctness itself is Python-only coverage per
§12 — `inject_frame` is not a Robot keyword.)

### 13.3 Hardware tests (future — not part of this Gate 1-3 pass)

Deferred until a real SLCAN adapter and CAN bus (or a second node to generate traffic) are
available for qualification: confirm the exact `F` status-flag bit layout against the target
adapter's own manual (§19); confirm the default serial baud rate the adapter's USB-CDC port
actually presents at (separate from, and not to be confused with, the CAN bitrate set via
`S<n>`); confirm real-world latency/throughput of the background reader under sustained bus
traffic; confirm behavior when the adapter is physically unplugged mid-session.

## 14. Documentation and examples

Deliver, matching this repository's other Gate 1-3 drivers: README with install, import,
quick start, safety notes, keyword reference, and status; four runnable Robot examples
(identify, open-and-transmit, receive-frames, status-and-error-handling). Full RFDS-005
documentation set (Pages/MkDocs, PyCharm/hardware setup guides, `ai/ai_contract.yaml`,
history, review) is Gate 4/5 work, matching every other new driver built this session.

## 15. Acceptance criteria

The task is complete only when:

- [ ] Required package naming and root structure are satisfied.
- [ ] No `src/` layout is used.
- [ ] RFDS-002 canonical connection keywords are the primary, documented connection API.
- [ ] Channel control, frame send/receive, status, and raw-escape-hatch keywords exist.
- [ ] The background reader thread correctly routes a frame injected mid-command to the
      receive queue rather than mistaking it for that command's ack.
- [ ] The background reader thread stops promptly on `close()`/`Disconnect`.
- [ ] Receive-queue overflow drops the oldest frame and increments a queryable counter.
- [ ] Closing the channel is always possible, even mid-fault.
- [ ] Raw SLCAN requires exact confirmation text.
- [ ] Python tests pass.
- [ ] Robot acceptance tests pass against the simulator.
- [ ] Offline examples pass.
- [ ] Static analysis (ruff, mypy) passes.
- [ ] Wheel and source distributions build.
- [ ] README is present and accurate.

Real-hardware SLCAN adapter qualification (§13.3) is a separate deployment gate, not an
offline software-generation defect — the release must remain labeled "hardware qualification
required" until it is completed.

## 16. Open questions for Gate 1 (need confirmation before/alongside core implementation)

1. **`F` status-flag bit layout** — the bit assignments in §2/`AdapterStatus` are drawn from
   the widely-mirrored Lawicel description but should be re-confirmed against the specific
   target adapter's own manual before relying on them for real bus-fault detection; different
   vendors have been observed to document this byte slightly differently.
2. **Serial baud rate vs. CAN bitrate** — the adapter's own USB-CDC/RS-232 link typically runs
   at a fixed baud rate (commonly 115200, used as this driver's default) that is entirely
   separate from the CAN bus bitrate set via `S<n>`; confirm the target adapter's actual
   default before hardware qualification rather than assuming 115200 universally.
3. **Open-without-bitrate rejection is a driver/simulator judgment call**, not a confirmed
   universal behavior — some real adapters may accept `O` and fall back to a previously-
   configured or default bitrate instead of rejecting it. This driver fails closed
   (conservative) rather than silently opening at an undefined rate; revisit if hardware
   qualification shows a specific target adapter behaves differently.
4. **CAN FD** — explicitly out of scope for v26.01 (§1); revisit only if a specific target
   adapter and its FD dialect are identified and its manual can be cited directly.

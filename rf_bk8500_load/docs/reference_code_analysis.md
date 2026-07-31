# Analysis of the supplied reference material


## Verification update

Release 26.16 preserves the v26.14 packet and echo-handling implementation reviewed here and adds ordered baud probing above it. A physical
Robot Framework run on model 8500 firmware 1.84 passed all 55 public keyword
tests and the list persistence workflow. The original report is preserved
under `evidence/hardware_conformance/v26.14_com12_2026-07-28/`.

This driver was written from the *8500 Series DC Electronic Loads* user manual
(version 032218), cross-checked against the vendor's example code
(`dcload.py`, `client.py`, `bk8500functions.py`, `8500pyserial.py`,
`8500List.py`, `8500CR_Transient_BusTrig.py`).

Where the example code and the manual disagree, **the manual wins** and the
decision is recorded below. Each item explains what this driver does instead.

## Defects found in the vendor reference code

| # | Where | Problem | Consequence | Handling in this driver |
|---|-------|---------|-------------|-------------------------|
| 1 | `dcload.py` `SetTriggerSource` | Sends command `0x54` (*set communication address*) instead of `0x58` (*select trigger source*) | Selecting the `bus` trigger silently sets the instrument's address to 2. Every later frame is addressed to 0 and is ignored, so the load appears to go dead | `set_trigger_source` uses `0x58`; `0x54` is only reachable through the address command, which is not exposed as a keyword |
| 2 | `dcload.py` `SetLoadOnTimerState` | Sends command `0x50` (*set timer value*) instead of `0x52` (*enable/disable timer*) | "Enable the timer" actually writes a timer value of 1 s and leaves the timer disabled | `set_load_on_timer_enabled` uses `0x52`; the value and the state are separate calls, combined in the `Set Load On Timer` keyword |
| 3 | `dcload.py` `SetTransient` / `GetTransient` | Uses `to_ms = 1000`, i.e. treats the dwell field as milliseconds | The manual defines the transient dwell field as 2 bytes in **0.1 ms** units, so every dwell is off by 10× | `COUNTS_PER_SECOND_DWELL = 1e4`; the round trip is asserted in `test_transient_roundtrip_uses_tenth_millisecond_units` |
| 4 | `dcload.py` `Initialize` | `serial.Serial(com_port - 1, baudrate)` | Legacy pyserial numeric port indexing, removed in pyserial 3.x. Also no timeout, so a missing instrument blocks forever | `SerialTransport` takes a device name, sets an explicit read and write timeout, and raises `BK8500TimeoutError` on a short read |
| 5 | `dcload.py`, `client.py` | Python 2 only (`print` statements, `xrange`, `from string import join`, `ord()` on `str`) | Does not run on any supported Python | Python 3.9+, `bytes` throughout, no string/byte ambiguity |
| 6 | `bk8500functions.py`, `8500pyserial.py` | Response checksum is never verified and the status byte is never checked | A corrupted or rejected command looks identical to a successful one | Every response is checked for length, start byte and checksum; every status frame is decoded and a non-`0x80` status raises `BK8500CommandError` |
| 7 | `8500CR_Transient_BusTrig.py` | No `timeout` set on the port; port hard-coded to `COM4` | A blocking read hangs the test runner | Timeout is a constructor argument, default 1 s; the port comes from the suite variables |
| 8 | `dcload.py` `SetFunction` | The `list` function (value 3) is deliberately omitted from the map | LIST operation cannot be selected at all | `LoadFunction` includes `LIST = 3`; `SHORT` is the one value gated behind an explicit override |
| 9 | `dcload.py` | Returns everything as strings, including tab-joined measurement tuples | Callers must parse text back into numbers; units are implicit | Typed dataclasses (`InputValues`, `ProductInfo`, `TransientSettings`, `ListStep`) with SI units; keywords return dictionaries Robot can index |
| 10 | `requirements.txt` | `pip install serial` | Installs an unrelated package; the import then fails or shadows pyserial | Declares `pyserial>=3.4` in `pyproject.toml` |
| 11 | `dcload.py` `CommandProperlyFormed` | Rejects a frame whose *address* byte is `0xFF`, but never checks the response | Only outgoing frames are validated | `frame_is_well_formed` is applied to both directions |
| 12 | All vendor scripts | None of them set DTR or RTS, relying on the serial library's default | The manual states both lines must be asserted. The default holds on most Windows/Prolific setups, which is why the scripts appear to work, but a driver that opens with the lines low produces a completely silent link and a bare timeout | `SerialTransport` asserts both explicitly, disables hardware and software flow control so the lines are never toggled as handshaking, and verifies the result on open |
| 13 | `dcload.py`, `client.py` | Accept any baud rate the OS will set | The firmware supports 4800, 9600, 19200 and 38400 only; higher rates give silence or corruption | `SerialTransport` rejects unsupported rates with `BK8500ConfigurationError` before opening the port |
| 14 | `8500List.py` | Writes step 2 twice with different values and never sets step 3 or 4 although the step count is 4 | Undefined steps play back as zero | `configure_list` derives indices from list order and writes every step, so the count and the programmed steps cannot disagree |

## Protocol facts taken from the manual

* Every frame is exactly 26 bytes: `0xAA`, address, command, 22 payload bytes,
  checksum = sum of the first 25 bytes mod 256.
* One response frame must be read for every request, including for commands
  that return no data. Skipping the read desynchronises the link.
* Scaling: voltage 1 mV/count, current 0.1 mA/count, power 1 mW/count,
  resistance 1 mΩ/count, transient and list dwell 0.1 ms/count, LOAD ON timer
  1 s/count.
* Status bytes: `0x80` success, `0x90` checksum incorrect, `0xA0` parameter
  incorrect, `0xB0` command cannot be carried out, `0xC0` invalid command.
* The operation-state register (byte 15 of a `0x5F` reply) carries the input
  state; the demand-state register (bytes 16–17) carries the protection flags
  and the active regulation mode.
* Address `0xFF` is reserved and must never appear in the address byte.
* The rear panel DB9 is **TTL**, not RS-232; a level-shifting adapter
  (IT-E132B) is mandatory and a direct RS-232 connection can damage the
  instrument.
* **DTR and RTS must be enabled/asserted** (manual, "USB (Virtual COM)
  settings"). Serial parameters are 8 data bits, 1 stop bit, no parity, and one
  of 4800, 9600, 19200 or 38400 baud.

## Model ratings used for validation

Taken from the manual's specification chapter. An unrecognised model falls back
to the smallest rating in the series (60 V, 15 A, 300 W), never to the largest.

| Model | Voltage | Current | Power |
|-------|---------|---------|-------|
| 8500 | 120 V | 30 A | 300 W |
| 8502 | 500 V | 15 A | 300 W |
| 8510 | 120 V | 120 A | 600 W |
| 8512 | 500 V | 30 A | 600 W |
| 8514 | 120 V | 240 A | 1200 W |
| 8518 | 60 V | 240 A | 1200 W |
| 8520 | 120 V | 240 A | 2400 W |
| 8522 | 500 V | 120 A | 2400 W |
| 8524 | 60 V | 240 A | 5000 W |
| 8526 | 500 V | 120 A | 5000 W |

## Deliberate omissions

* **Calibration commands `0x60`–`0x69`.** A mis-issued calibration command
  writes the instrument's EEPROM. Calibration belongs to the vendor's tools.
* **Bar code command `0x6B`.** No documented use in a test context.
* **Communication address `0x54`.** Changing the address mid-session breaks the
  running connection; it is a bench provisioning step, not a test step.

# Changelog

Two version values are recorded:

* **Package/Python release** — ZIP `rf_bk8500_load_v26.<release>.zip` installs as
  Python version `26.<release>.0` starting with release 11.
* **Lifecycle version** — `vYY.PP.GG`, retained separately as RFDS phase/gate
  metadata. Releases 6–10 used lifecycle-derived `.postN` Python versions; this
  confusing scheme is preserved only as historical data.

| Release | Driver version | Lifecycle stage |
|---|---|---|
| 17 | 26.17.0 | Phase 1, Gate 5 maintenance revision 12 |
| 16 | 26.16.0 | Phase 1, Gate 5 maintenance revision 11 |
| 15 | 26.15.0 | Phase 1, Gate 5 maintenance revision 10 |
| 14 | 26.14.0 | Phase 1, Gate 5 maintenance revision 9 |
| 13 | 26.13.0 | Phase 1, Gate 5 maintenance revision 8 |
| 12 | 26.12.0 | Phase 1, Gate 5 maintenance revision 7 |
| 11 | 26.11.0 | Phase 1, Gate 5 maintenance revision 6 |
| 10 | 26.1.5.post5 | Phase 1, Gate 5 maintenance revision 5 |
| 9 | 26.1.5.post4 | Phase 1, Gate 5 maintenance revision 4 |
| 8 | 26.1.5.post3 | Phase 1, Gate 5 maintenance revision 3 |
| 7 | 26.1.5.post2 | Phase 1, Gate 5 maintenance revision 2 |
| 6 | 26.1.5.post1 | Phase 1, Gate 5 maintenance revision 1 |
| 5 | 26.01.05 | Phase 1, Gate 5 |
| 4 | 26.01.04 | Phase 1, Gate 4 |
| 3 | 26.01.03 | Phase 1, Gate 3 |
| 2 | 26.01.02 | Phase 1, Gate 2 |
| 1 | 26.01.01 | Phase 1, Gate 1 |

## 26.17.0 — package release 17

Added a live, always-on RFDS-008 evidence engine (`bk8500_load/evidence.py`):
every public keyword call is now recorded (arguments, duration, result/
failure) together with a frame-level protocol trace of every 26-byte command/
response exchanged with the load, written to a timestamped, SHA-256-hashed
run directory under `results/session/bk8500_load/`. This is a new,
complementary system distinct from the existing archived
`evidence/hardware_conformance/` example. Added the `Export Diagnostic
Bundle` keyword (public keyword count is now 62), `schemas/evidence/`,
`docs/logging_and_evidence.md` and `guide/logging_and_evidence.md`,
`scripts/validate_evidence.{py,sh,bat,ps1}`, and `tests/evidence/`. Added
`KW-061 Export Diagnostic Bundle` to the hardware conformance suite
(`hardware_tests/01_all_library_keywords.robot`, now 62 Robot test cases) and
an `OperatingSystem` library import it needed. Updated the RFDS-017 contract
(revision 13) and regenerated its integrity lock.

## 26.16.0 — package release 16

Added optional automatic baud-rate detection to `Open Load Connection`. The
requested numeric baud is tried first, followed by unique supported candidates.
Detection sends only the read-only product-information query, rejects local
echo, malformed/empty responses and inconsistent identities, closes failed
serial handles, and records the selected baud plus attempt evidence. Fixed-baud
behaviour remains the default and the public keyword count remains 55.

## 26.15.0 — package release 15

- Preserve the complete 56/56 physical COM12 Robot Framework report.
- Add machine-readable environment, device, keyword coverage, expected
  negative-message, and evidence-integrity files.
- Record closure of all 55 public keyword tests and the list persistence
  workflow on model 8500 firmware 1.84.
- Update every current package document, GitHub Pages, AI metadata, history,
  review, manifest, and lifecycle gate report.
- Keep protocol, transport, driver, compatibility module, and keyword API
  functionally unchanged from v26.14.
- State explicitly that RFDS-019 raw protocol trace and injected-fault coverage
  remain separate deliverables.

## 26.14.0 — package release 14

Aligned serial opening with the proven COM12 bench script: DTR and RTS are
requested before open, reasserted after open, and followed by a one-second
settle. Added local-echo handling: exact write-request echoes are discarded
while the transport waits for the protocol-required `0x12` status response.
Echo without a following device response now raises a targeted timeout, and an
empty product-information payload is rejected as an echoed-query signature.
Added a raw serial echo diagnostic and regression tests based on the uploaded
remote (`0x20`) and fixed-function (`0x5D`) packets. The 55-keyword public API
is unchanged.

## 26.13.0 — package release 13

Responded to the physical v26.12 result where all 55 public keywords passed but
the supplemental persistence workflow failed because firmware 1.84 rejected a
one-step list at command `0x3E`. The driver now requires two or more list steps
before protocol traffic, the simulator mirrors the same limit, and the workflow
uses a valid two-step replacement profile. Added RFDS-019 v1.1 to the packaged
AI specifications. The public keyword API is unchanged.

## 26.12.0 — package release 12

Responded to the physical COM9 result (54/55) where command `0x3E` was
rejected immediately after saving a list file. Added EEPROM settle barriers,
partition-aware list and slot validation, forced input-OFF list editing, richer
`0x3E` diagnostics, stateful simulator list persistence, software/device version
evidence, stale-install rejection, and a dedicated save → reconfigure → recall
workflow regression. The 55-keyword public API is unchanged.

## 26.11.0 — package release 11

Added a real-device Robot Framework conformance suite with one test for every
public keyword, readback/status verification, cross-platform runners and
explicit safety gates for input enable and persistent storage writes. Added an
executable simulator regression that invokes all 55 keywords and fails on API
coverage drift. Corrected the Python distribution version so ZIP release v26.11
installs as `bk8500-load==26.11.0`; lifecycle phase/gate metadata remains
separate.

## 26.1.5.post5 — package release 10

Fixed the delivered Robot examples that use `Log Dictionary`. The shared example
resource now imports Robot Framework's `Collections` library, making the keyword
available to examples 01 and 05. Environment validation now dry-runs the entire
`examples/` directory in addition to the public driver import, preventing missing
standard-library imports from reaching a release. The driver keyword API is
unchanged.

## 26.1.5.post4 — package release 9

Fixed Robot Framework short-name library discovery. `BK8500Library.py` now
defines a local subclass so `Library    BK8500Library` exposes all 55 keywords
instead of being treated as an empty module library. Added a Robot dry-run
import smoke test to environment selection and regression tests for the exact
setup/teardown keywords reported missing. The public keyword signatures are
unchanged.

## 26.1.5.post3 — package release 8

Added direct PowerShell, batch, and shell launchers inside `examples/`. Added
runtime environment verification and automatic repair for missing Robot
Framework, pyserial, or editable driver installation. The canonical runners now
bootstrap the package-private `.venv` before execution and pass both simulator
selection and serial port consistently. Added package tests, release history,
and review evidence for this correction. The 55-keyword API is unchanged.

## 26.1.5.post2 — package release 7

Removed the intermediate `src/` directory and adopted the requested flat layout:
`bk8500_load/` for implementation and root `ai/` for all AI-facing deliverables.
Added an AI integration README and the governing RFDS-017, RFDS-018, and
lifecycle specifications. Updated source/wheel contract discovery, package
metadata, documentation, tests, and release evidence. The Robot keyword surface
remains unchanged. See `history/release_v26.7.md` and
`review/release_v26.7_structure_and_ai_review.md`.

## 26.1.5.post1 — package release 6

Added the mandatory project delivery structure, twelve examples, cross-platform
runners, setup guides, GitHub Pages/CI assets, licence, and package-structure
tests. Fixed duplicate alias leakage, failed-identification transport cleanup,
and source-only RFDS keyword conformance metadata. See
`history/release_v26.6.md` and `review/release_v26.6_code_review.md`.

## v26.01.05 — Phase 1, Gate 5 (Review & Release)

Code-review response to v26.01.04. No new features; see `RELEASE_NOTES.md` and
`review/phase1_gate5_code_review.md`.

Fixed
- Read replies whose command byte is not an echo of the request are accepted
  (R-1, critical): the manual does not specify the reply framing for read
  commands, and the previous strictness would have failed every read keyword on
  firmware that tags replies `0x12`. The observed style is reported as
  `response_style`; a status frame with no payload remains an error rather than
  a guess.
- `BK8500TimeoutError` is retried, as the contract already claimed (R-2).
- List programming validates the whole profile before writing any step, so a
  rejected profile can no longer leave a step count that disagrees with the
  steps written (R-3).
- The RFDS-017 contract now lives inside the package and ships in the wheel;
  `contract_path()` and `lock_path()` locate it (R-4).
- Replies are checked against the addressed instrument (R-5).
- The stabilization delays declared per capability are applied by the driver,
  and can be disabled with `apply_stabilization_delays=False` (R-6).
- Closing the current connection clears it instead of silently adopting another
  alias (R-7).
- The lock generator refuses to write an empty keyword surface (R-8).
- Booleans are rejected where a number is required (R-9).
- Raw firmware bytes exposed as `firmware_raw`, pending confirmation of hex
  versus BCD encoding on hardware (R-11).

## v26.01.04 — Phase 1, Gate 4 (Tests & Documentation)

Fixed
- `SerialTransport` now asserts DTR and RTS explicitly on open and verifies
  them, instead of relying on the serial library's platform-dependent default.
  The manual requires both lines asserted; without them the link is silent and
  every transaction times out with no error from the instrument. Hardware and
  software flow control are disabled explicitly so the lines are never toggled
  as handshaking. Exposed as `assert_dtr` / `assert_rts` on
  `Open Load Connection`, and reported by `Get Load Connection Info`.
- Corrected the supported baud rates to 4800, 9600, 19200 and 38400. Rates
  above 38400 were previously accepted and are now rejected with
  `BK8500ConfigurationError`.

Added
- Unit test suite (`tests/test_driver.py`): protocol codec against the manual's
  worked examples, validation, safety interlocks, mode physics, transient and
  list round trips, retry behaviour, stability waiting, multi-connection handling.
- Contract conformance suite (`tests/test_contract_conformance.py`) enforcing
  conformance rules CR-1..CR-7.
- Robot Framework conformance suite (`atest/`) with a shared resource file
  implementing the setup/teardown contract.
- Architecture, user guide and reference-code analysis documents.
- Keyword documentation generated with libdoc.

## v26.01.03 — Phase 1, Gate 3 (Extended Features)

Added
- Transient operation (0x32–0x39) with correct 0.1 ms dwell scaling.
- List operation (0x3A–0x4D): mode, repeat, step count, per-step programming,
  file name, partition, save and recall.
- Battery test cut-off voltage and the LOAD ON timer.
- Settings storage registers 1–25.
- `Wait Until Load Reading Is Stable` with a sliding peak-to-peak window.
- Multi-instrument support through connection aliases.
- `SimulatedTransport` extended to the full command set used by the driver.
- `ai/ai_contract.yaml` completed to RFDS-017 v3.0, plus `ai_contract.lock`.

## v26.01.02 — Phase 1, Gate 2 (Core Implementation)

Added
- `BK8500Driver`: remote control, input state, protection limits, the four
  regulation modes and their setpoints, function selection, triggering,
  measurement and product identity.
- `BK8500Library` keyword layer with verification keywords.
- Safety rules: remote-control interlock on `Load Input On`, SHORT guard,
  envelope validation with a conservative fallback for unknown models.
- Error catalogue and response status decoding.

## v26.01.01 — Phase 1, Gate 1 (Architecture & Skeleton)

Added
- Package skeleton, `pyproject.toml`, buildable wheel.
- `protocol.py`: 26 byte frame codec, command table, status codes, unit constants.
- `transport.py`: `Transport` base plus `SerialTransport` and `SimulatedTransport`.
- `enums.py`, `exceptions.py`, model capability table.

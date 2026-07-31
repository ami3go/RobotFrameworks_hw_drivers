# Phase 1 gate report — current status

Package: `rf_bk8500_load_v26.16.zip`  
Distribution: `bk8500-load==26.16.0`  
Lifecycle: Phase 1, Gate 5 maintenance revision 11

## Gate summary

| Gate | Status | Evidence |
|---|---|---|
| Gate 1 — foundation | PASS | package, protocol codec, exceptions, simulator |
| Gate 2 — core driver/API | PASS | 55 Robot keywords and Python driver |
| Gate 3 — extended features | PASS | transient, list, battery, timer, storage |
| Gate 4 — tests/documentation | PASS | unit tests, examples, guides, AI contract |
| Gate 5 — hardware callability/release | PASS with documented scope | 56/56 physical Robot tests and preserved evidence |

## Physical closure

The v26.14 functional core passed all 55 public keyword tests plus the
save/reconfigure/recall list workflow on B&K Precision 8500 serial
`1687710135`, firmware `1.84`, COM12 at 9600 baud. Suite setup, identity,
version matching, readbacks, negative paths, and safe teardown passed.

Finding F-1 (no physical keyword verification) is closed. Reply style and
firmware parsing were observed successfully: `response_style=echo`,
firmware bytes `[1, 132]`, parsed as `1.84`.

## Current release relationship

Release 26.16 preserves the v26.14 packet, echo-handling and command path and
adds optional read-only automatic baud detection in the connection layer.
Fixed numeric baud remains the default. Unit, simulator, contract, cleanup and
packaging checks pass; physical fallback detection at a deliberately changed
front-panel baud remains follow-up evidence.

## Remaining scope

These items do not invalidate the 56/56 keyword callability result:

- raw per-keyword TX/RX protocol traces and vector result files required for
  full RFDS-019 Levels 2–4;
- injected malformed-frame, timeout, disconnect, and recovery vectors;
- multi-baud performance characterisation;
- independent electrical accuracy and regulation testing.

## Release decision

**Approved for controlled project use and release.** Full protocol-trace
conformance and physical performance qualification remain separately
tracked follow-up work.

## Release v26.16 maintenance addition

Optional read-only automatic baud detection passed code, contract, simulator, cleanup, and packaging review. Physical fallback confirmation remains a documented follow-up.

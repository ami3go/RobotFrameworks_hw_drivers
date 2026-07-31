# Physical hardware conformance evidence — v26.14 on COM12

## Verdict

**PASS — 56 of 56 Robot Framework tests passed on the physical B&K Precision 8500.**

The run verifies all 55 exported public Robot Framework keywords plus the
`WF-001 Save Reconfigure And Recall List` cross-keyword persistence workflow.

## Environment

| Field | Value |
|---|---|
| Report generated | 2026-07-28T18:08:18.443613 |
| Suite start | 2026-07-28T18:08:18.508058 |
| Suite duration | 87.159538 s |
| Host | Windows-11-10.0.22631-SP0 |
| Python | 3.13.5 |
| Robot Framework | 7.4.2 |
| Driver source version | 26.14.0 |
| Installed distribution version | 26.14.0 |
| Transport | COM12 at 9600 baud, address 0 |

## Device identity

| Field | Value |
|---|---|
| Model | 8500 |
| Serial number | 1687710135 |
| Firmware | 1.84 |

## Results

| Test class | Passed | Failed |
|---|---:|---:|
| Public keyword tests | 55 | 0 |
| Persistence workflow | 1 | 0 |
| **Total** | **56** | **0** |

The two `FAIL`-level log messages are expected negative-path assertions wrapped
by Robot Framework's `Run Keyword And Expect Error`:

1. selecting a closed/unknown alias;
2. querying connection information after all connections are closed.

Both enclosing tests passed.

## Scope statement

This evidence closes physical-device keyword callability and the declared
save/reconfigure/recall workflow for driver version `26.14.0`. It confirms
successful communication through the echo-aware COM12 path, non-empty identity,
command/readback operation, and safe teardown.

It is not, by itself, a complete RFDS-019 Level 2–4 evidence bundle because the
run does not include per-keyword raw TX/RX traces, protocol-vector result files,
or injected timeout/malformed-frame recovery evidence. Those remain separate
protocol-observation deliverables.

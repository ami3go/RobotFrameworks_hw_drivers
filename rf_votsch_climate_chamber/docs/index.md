# RFDS Vötsch Climate Chamber Driver v26.09

This site documents the canonical API 3.0 cleanup release. The runtime exposes
58 explicit Robot Framework keywords, deterministic simulation, TCP transport,
safety limits, configuration profiles, plugin metadata, AI contracts, and
protocol-conformance artifacts.

API 2 compatibility aliases and the duplicate legacy Python package were removed
at the user's direction. Real-device support remains unqualified until exact
model and firmware evidence is recorded.

Release v26.09 adds a live RFDS-008 evidence engine (`evidence.py`): every keyword
call and every SimServ protocol frame is recorded to a correlated,
SHA-256-integrity-checked run, reusing the existing `TraceObserver` mechanism rather
than re-instrumenting the transport layer. See
[Evidence and diagnostics](TROUBLESHOOTING.md#evidence-and-diagnostics-which-one-do-i-want)
for how this differs from the pre-existing point-in-time `Get/Export Diagnostics`
snapshot.

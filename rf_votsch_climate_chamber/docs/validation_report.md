# Validation Report — v26.08

The release builder validates metadata synchronization, package structure, compilation, Python tests, branch-aware coverage, simulator workflow, distributions, clean installation, and fixed-root ZIP creation.

The v26.08 regression suite specifically verifies:

- delayed setpoint readback eventually succeeds;
- setpoint verification timeout contains actionable evidence;
- unconfigured auxiliary outputs fail before protocol transmission;
- safe shutdown skips unconfigured auxiliary outputs and stops the chamber;
- configured simulator auxiliary outputs remain functional;
- effective configuration is round-trippable;
- close-only disconnect does not alter simulated chamber state.

Native Robot and physical-chamber results remain target-environment gates and are not inferred from Python tests.

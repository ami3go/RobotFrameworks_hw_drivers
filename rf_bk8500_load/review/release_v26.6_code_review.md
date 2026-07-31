# Code review — release v26.6

## Scope

Maintenance changes in `library.py`, `driver.py`, contract metadata, tests,
examples, scripts, guides, and GitHub delivery assets.

## Review results

### CR-26.6-01 — fallback keyword metadata

The fallback decorator now writes `robot_name`, `robot_tags`, and `robot_types`
onto decorated functions. This mirrors the metadata used by conformance tests
without attempting to emulate Robot execution. Result: source-only pytest can
verify the RFDS-017 keyword surface.

### CR-26.6-02 — duplicate alias guard

`Open Load Connection` validates the alias before opening a new transport. This
prevents replacement of an existing entry and loss of the only reference to an
open serial connection. The original connection remains current and usable.

### CR-26.6-03 — failed identify cleanup

`BK8500Driver.connect()` now closes the transport if the initial identity query
raises. The original exception is re-raised, preserving diagnostics. The fix is
limited to identification failure; `identify=False` intentionally leaves the
opened transport available.

### CR-26.6-04 — examples and launchers

All examples default to `SIMULATED=True`, use suite teardown, and avoid the
unchecked SHORT keyword. Hardware execution requires an explicit command-line
override. Scripts resolve their own project root and place output under
`results/`.

## Open risk

Serial framing and physical behaviour have still not been verified against a
real B&K 8500-series load. Simulator success is not evidence of hardware
compatibility.

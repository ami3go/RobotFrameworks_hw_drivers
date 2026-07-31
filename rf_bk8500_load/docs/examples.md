# Examples


The driver API used by these examples has a 56/56 physical conformance
baseline. Examples remain simulator-first; a passing example is not a
substitute for an RFDS-018 bench safety review.

Twelve Robot Framework examples are delivered in the package `examples/`
directory. They default to the simulator and are numbered in learning order.

1. Identity and rated limits
2. Constant current
3. Constant voltage
4. Constant power
5. Constant resistance
6. Transient mode
7. List mode
8. Battery cut-off and timer
9. Measurement oracles
10. Multiple load aliases
11. Safe teardown
12. Settings storage

Run one example with `scripts/run_example.*` or all examples with
`scripts/run_all_examples.*`.

## 13 — Automatic baud detection

Attempts the preferred rate and configured fallbacks using only identity
queries, then logs the detected baud and product identity. The suite skips by
default because examples use simulation unless explicitly changed.

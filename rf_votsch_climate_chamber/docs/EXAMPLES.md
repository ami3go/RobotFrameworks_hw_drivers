# Robot Framework Examples

The `examples/` directory contains 13 complete suites:

1. `01_basic_control.robot` — connect, identify, read, set, start, and stop.
2. `02_safe_suite_lifecycle.robot` — suite setup and failure-safe teardown.
3. `03_temperature_safety_limits.robot` — verify local safety enforcement.
4. `04_set_stabilize_and_dwell.robot` — setpoint, stability samples, and dwell.
5. `05_wait_without_changing_setpoint.robot` — observe an existing setpoint.
6. `06_temperature_cycle.robot` — execute multiple temperature stages.
7. `07_gradient_control.robot` — heating and cooling gradients.
8. `08_auxiliary_outputs.robot` — dryer and compressed-air control.
9. `09_health_and_statistics.robot` — health snapshot and communication counters.
10. `10_reconnect_after_network_event.robot` — explicit reconnect workflow.
11. `11_chamber_specific_assertions.robot` — instrument-aware assertions.
12. `12_file_configuration.robot` — external variable-file configuration.
13. `13_failure_safe_teardown.robot` — cleanup after a deliberate test failure.

## Run examples

List examples:

```bash
python scripts/run_example.py --list
```

Dry-run one example:

```bash
python scripts/run_example.py 4 --dryrun
```

Dry-run all examples:

```bash
python -m robot --dryrun --pythonpath . --outputdir results/examples examples
```

The example runner also accepts repeated Robot variables:

```bash
python scripts/run_example.py 1 \
  --variable CHAMBER_IP:192.168.1.50 \
  --variable TEMP_MIN:-40 \
  --variable TEMP_MAX:180
```

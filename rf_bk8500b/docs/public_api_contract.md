# Public API contract v1.0

The root package exports the symbols listed in specification section 9 and captured in `tests/api_contract/v1_0.json`. Removing or renaming a stable symbol requires a major release.

## Primary classes

```python
BK8500B(config, *, transport=None, audit_sink=None, metrics_sink=None)
AsyncBK8500B(config, *, transport=None, audit_sink=None, metrics_sink=None)
```

Construction validates only; it does not open a port.

## Advanced model fields

- `TransientConfig(high_level, high_dwell_s, low_level, low_dwell_s, slew_a_per_us, mode)`
- `LEDConfig(voltage_v, current_a, resistance_coefficient)`
- `OCPTestConfig(start_current_a, end_current_a, steps, dwell_s, trigger_voltage_v)`
- `OCPTestResult(ocp_current_a, maximum_power_w, voltage_at_maximum_v, current_at_maximum_a)`
- `TimingTestConfig(load_setting_enabled, mode, value, start_source, start_edge, start_level, end_source, end_edge, end_level)`
- `TimingTestResult(duration_s)`
- `ListConfig(steps, repeat_count)` where every step is `ListStep(current_a, dwell_s)` from `bk8500b.measurements`
- `ListRunResult(completed, maximum_voltage_v, minimum_voltage_v, maximum_current_a, minimum_current_a, experimental=True)`

Legacy list, battery, and autotest are not stable despite reserved type names. Stable methods raise `UnsupportedFeatureError` until their command-policy rows have HIL evidence.

## Exception behavior

All driver exceptions derive from `BK8500BError` and carry immutable `.context`. `IndeterminateCommandOutcome` means callers must query/reconcile state rather than repeat the command.

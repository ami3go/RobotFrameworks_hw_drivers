# Configuration

The authored schema is `config/schema.json`; runtime copies are packaged under `rf_votsch_climate_chamber/resources/`.

## Write verification

```yaml
settings:
  operation:
    verify_writes: true
    setpoint_verify_tolerance_c: 0.05
    setpoint_verify_timeout_s: 15.0
    setpoint_verify_poll_interval_s: 0.25
```

A setpoint write is acknowledged first and then verified by repeated readback. Failure remains strict, but it occurs only after the configured finite timeout.

## Auxiliary outputs

```yaml
settings:
  auxiliary_outputs:
    dryer_output_channel: null
    compressed_air_output_channel: null
    fan_output_channel: null
```

`null` is the safe default for real hardware. Configure a channel only after confirming the mapping for the exact chamber model and firmware. No two of these functions may share one channel and channel 1 is reserved for chamber running state.

## Round-trip behavior

`Get Driver Configuration` may include runtime annotations such as `configuration_fingerprint`. The same result can be passed back to `Validate Driver Configuration` or `Import Driver Configuration`; these known read-only annotations are ignored with a warning. Unknown fields remain rejected by the schema.

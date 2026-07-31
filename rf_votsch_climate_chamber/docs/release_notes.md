# Release Notes — v26.08

v26.08 hardens real-hardware write verification and teardown behavior without changing the canonical API 3.0 keyword names.

## Fixed

- delayed setpoint readback no longer causes an immediate false failure;
- effective configuration can be modified and re-imported;
- close-only hardware teardown is actually applied and verified;
- safe shutdown does not transmit unknown dryer/compressed-air channel commands;
- auxiliary API verification is explicitly mapping- and authorization-gated.

## Added

- `setpoint_verify_timeout_s`;
- `setpoint_verify_poll_interval_s`;
- `dryer_output_channel` and `compressed_air_output_channel` configuration;
- seven targeted hardware-regression unit tests.

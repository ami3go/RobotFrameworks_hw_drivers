# Troubleshooting

## `Set Temperature` reports the previous setpoint

Some chamber controllers acknowledge the write before the public setpoint register updates. The driver therefore polls readback for a finite interval instead of checking only once.

1. Confirm that the chamber is in remote-control mode.
2. Check whether a running program, profile, or local operator lock owns the setpoint.
3. Review the failure details: requested value, last reported value, attempt count, and elapsed time.
4. Keep `setpoint_verify_tolerance_c` narrow enough to prove the write was accepted.
5. Increase `setpoint_verify_timeout_s` only when controller behavior justifies it; do not disable verification.

## Dryer or compressed-air command is rejected

Auxiliary output channels are model- and wiring-dependent. The driver no longer assumes channels 7 and 8 for real TCP hardware.

- Leave `settings.auxiliary_outputs.dryer_output_channel` and `compressed_air_output_channel` as `null` until the exact mapping is qualified.
- An unconfigured auxiliary keyword fails locally with `DriverUnsupportedOperationError`; no command is transmitted.
- Safe shutdown marks an unconfigured auxiliary action `SKIP` and still stops the chamber.
- Configure a channel only after verifying the chamber model, firmware, electrical function, and safe-state polarity.

## Disconnect unexpectedly changes chamber state

`Disconnect` follows `settings.safety.safe_shutdown_on_disconnect`. Set it to `false` only for a workflow that explicitly restores state before closing the transport. When importing a dictionary returned by `Get Driver Configuration`, the library removes its read-only runtime annotations and validates the remaining configuration before applying it. Always assert both `valid` and `applied` in a Robot suite.

## Common error families

- `RFDS-CON-001`: verify host, TCP port 2049, routing, and chamber service.
- `RFDS-TRN-*`: inspect TCP connectivity and reconnect explicitly.
- `RFDS-PRO-*`: capture trace and compare it with the protocol vectors.
- `RFDS-ARG-*`: correct the local argument type or range; no command was sent.
- Stabilization timeout: inspect target, chamber load, tolerance, polling interval, and finite timeout.
- Robot import failure: install the project into the active interpreter and verify with `python -c "import rf_votsch_climate_chamber"`.

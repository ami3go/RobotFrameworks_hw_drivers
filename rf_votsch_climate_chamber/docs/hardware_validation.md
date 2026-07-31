# Hardware Validation

Real-device validation must record model, serial number, firmware, transport endpoint, temperature limits, original and restored state, and protocol evidence.

## Setpoint readback

The hardware smoke suite allows up to 30 seconds for the chamber's public setpoint register to reflect an acknowledged write. If it remains unchanged, inspect local/remote control mode, access permissions, active program state, and controller-specific setpoint behavior before increasing the timeout.

## Auxiliary outputs

Do not assume channels 7 and 8. Keep `DRYER_OUTPUT_CHANNEL` and `COMPRESSED_AIR_OUTPUT_CHANNEL` as `${NONE}` unless the exact mapping is qualified. State-changing auxiliary tests additionally require `ALLOW_AUXILIARY_OUTPUTS=True`.

No chamber model is declared production-qualified until representative D2/P1 evidence is recorded.

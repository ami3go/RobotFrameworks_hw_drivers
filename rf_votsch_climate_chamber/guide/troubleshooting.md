# Troubleshooting

## Set Temperature reports the old setpoint

v26.08 polls readback for a finite interval. If the error still reports the old value after the timeout:

1. Confirm the chamber is in remote/manual-control mode accepted by the SimServ interface.
2. Check whether a running program or local operator lock owns the setpoint.
3. Verify that command 11001 is permitted for control variable 1 on this model.
4. Capture the protocol trace from `Get Diagnostics`.
5. Increase `setpoint_verify_timeout_s` only when the vendor/controller behavior justifies it.

Do not disable write verification merely to make the test pass unless another independent readback oracle is used.

## Safe Shutdown reports status -8 for dryer

The chamber rejected an assumed digital-output mapping. Leave the output channel as `null`; v26.08 then skips it safely. Configure a channel only after the model-specific mapping is confirmed.

## Disconnect still changes chamber state

Check the result of `Import Driver Configuration`; both `valid` and `applied` must be true. v26.08 accepts the output of `Get Driver Configuration` for round-trip import and records ignored runtime annotations as warnings.

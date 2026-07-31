# Safety

Temperature values are rejected locally outside configured limits before transmission.

## Setpoint verification

`Set Temperature` polls setpoint readback until it matches the requested value within tolerance or until `setpoint_verify_timeout_s` expires. It never silently accepts a stale setpoint. A timeout reports the requested and reported temperatures, attempts, and elapsed time.

## Safe shutdown

`Safe Shutdown` always attempts to stop the chamber. Dryer and compressed-air outputs are disabled only when their physical output channels were explicitly configured. Missing mappings produce `SKIP` evidence, not an unqualified protocol write.

`Disconnect` and suite-end cleanup obey `settings.safety.safe_shutdown_on_disconnect`. Hardware tests that restore an original running state use close-only disconnect so cleanup does not undo that restoration.

This software is not a substitute for independent over-temperature protection, emergency isolation, or the chamber's local safety controls.

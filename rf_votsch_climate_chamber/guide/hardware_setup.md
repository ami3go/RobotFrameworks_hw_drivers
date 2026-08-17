# Hardware Setup

Connect the chamber and test computer to an isolated laboratory network. Confirm the IP address, TCP port, exact chamber model, firmware, operating limits, independent safety interlocks, and emergency-stop procedure.

Begin with `Check Communication`, `Get Identity`, and read-only queries. Configure a finite setpoint readback timeout appropriate for the controller; v26.08 defaults to 15 seconds and the supplied hardware smoke suite uses 30 seconds.

## Auxiliary outputs

Do not assume that digital outputs 7 and 8 represent compressed air and dryer. Configure these only after the mapping is qualified on the exact chamber:

```yaml
settings:
  auxiliary_outputs:
    dryer_output_channel: null
    compressed_air_output_channel: null
```

Replace `null` only with verified channel numbers. Until then, auxiliary keywords are unavailable and safe shutdown skips those actions rather than transmitting an unqualified command.

## Disconnect policy

Normal production teardown may use safe shutdown. A validation suite that deliberately restores the chamber's original running state must set `safe_shutdown_on_disconnect: false` before connecting, verify that the configuration import was valid and applied, and then perform a close-only disconnect.

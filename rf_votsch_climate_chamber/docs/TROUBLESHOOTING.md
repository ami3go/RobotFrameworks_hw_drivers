# Troubleshooting

## Connection refused

- Confirm IP address and TCP port, normally 2049.
- Ping only proves IP reachability, not chamber protocol availability.
- Check chamber remote-control settings and firewall rules.
- Verify another client is not holding an exclusive session.

## Timeout or partial response

- Increase `timeout` and `response_timeout` separately.
- Check cables, switches, VLANs, and power-save behavior.
- Read `Get Climate Chamber Connection Statistics`.
- Capture the Robot DEBUG log before increasing retry count excessively.

## Setpoint verification failed

The write command completed but readback differs from requested value. Check chamber resolution, remote/local control mode, controller limits, and whether another controller is writing setpoints.

## Chamber starts but keyword times out

Increase `state_change_timeout` in driver-level Python use if the controller reports state slowly. Confirm digital output channel 1 matches manual mode for the chamber firmware.

## Stabilization never completes

- Confirm the chamber is running.
- Check target is physically reachable.
- Increase tolerance or timeout only when justified.
- Reduce `stable_samples` for smoke tests, not for qualification tests.
- Check DUT heat load and sensor placement.

## Import or Libdoc tries to connect

Use the Robot adapter class, not the raw `ClimateChamber` class. Adapter construction is intentionally offline.

## Packaging version appears as 26.2

This is correct PEP 440 normalization of the human release label `v26.02`.
